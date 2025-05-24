from datetime import datetime, timezone
import asyncio, aiofiles
import time, os
from functools import wraps

import aiohttp

from settings import API_HEADER_FIELDS
from utils.log import api_logger, logger
from utils.errors import ErrorFetchingData, UnableToDecodeJson
import json
from collections import deque
FILE_LOCK = asyncio.Lock()


class AsyncRateLimiter:
    def __init__(self, api_type):
        self.api_type = api_type
        self.remaining_calls = API_HEADER_FIELDS[api_type]["rate_limit"]
        self.reset_time = 0
        self.lock = asyncio.Lock()


    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.lock:
                if self.api_type != "kovaaks":
                    current_time = time.time()

                    # If reset time has passed, reset our counter
                    if current_time > self.reset_time:
                        self.remaining_calls = API_HEADER_FIELDS[self.api_type]["rate_limit"]

                    # Wait if we're out of calls
                    if self.remaining_calls <= 5:
                        wait_time = max(float(0), self.reset_time - current_time)
                        if wait_time > 0:
                            api_logger.warning(f"Hit {self.api_type} rate limit waiting {wait_time} seconds.")
                            await asyncio.sleep(wait_time)
                            self.remaining_calls = API_HEADER_FIELDS[self.api_type]["rate_limit"]

            # Execute the API call
            data, headers = {}, {}
            runtime = -1000
            try:
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                runtime = end_time - start_time
                data, headers = result
                return data
            except Exception as e:
                if hasattr(e, "context"):
                    headers = e.context.get("headers", {})
                raise e
            finally:
                if self.api_type != "kovaaks":
                    await self.update_calls(headers, func, runtime)
                else:
                    api_logger.info(f"Made call to {self.api_type} api from function "
                                    f"{func.__name__} ({runtime:.2f} s): rate limit "
                                    f"N/A, reset_time N/A")

        return wrapper


    async def update_calls(self, headers, func, runtime):
        async with self.lock:
            try:
                self.remaining_calls = int(headers.get(
                    API_HEADER_FIELDS[self.api_type]["rate_limit_field"]))

                reset_time = float(headers.get(
                    API_HEADER_FIELDS[self.api_type]["reset_time_field"]))
                api_logger.info(f"Made call to {self.api_type} api from function "
                            f"{func.__name__} ({runtime:.2f} s): rate limit "
                            f"{self.remaining_calls}, reset_time "
                            f"{reset_time:.2f} s.")
                self.reset_time = time.time() + reset_time
            except Exception as e:
                api_logger.error(f"Failed to update rate limit for "
                             f"{self.api_type}: {e}")


class UpdatedAsyncRateLimiter:
    def __init__(self, api_type):
        self.api_type = api_type
        self.lock = asyncio.Lock()

        # Get rate limit config
        config = API_HEADER_FIELDS[api_type]
        self.max_calls = config["rate_limit"]
        self.window_size = 60  # 1 minute window

        # Token bucket approach
        self.tokens = self.max_calls
        self.last_refill = time.time()

        # Track call history for sliding window
        self.call_history = deque()

        # Exponential backoff for 429 errors
        self.consecutive_429s = 0
        self.last_429_time = 0

        # API-specific settings
        self.has_rate_limit = api_type != "kovaaks"
        if self.has_rate_limit:
            self.rate_limit_field = config["rate_limit_field"]
            self.reset_time_field = config["reset_time_field"]

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.has_rate_limit:
                # No rate limiting for APIs like kovaaks
                return await self._execute_call(func, *args, **kwargs)

            # Wait for rate limit clearance
            await self._wait_for_rate_limit()

            # Execute with retry logic
            max_retries = 3
            base_delay = 1.0

            for attempt in range(max_retries + 1):
                try:
                    return await self._execute_call(func, *args, **kwargs)
                except Exception as e:
                    if self._is_rate_limit_error(e):
                        if attempt == max_retries:
                            raise

                        # Handle 429 with exponential backoff
                        await self._handle_429_error()
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise

        return wrapper

    async def _wait_for_rate_limit(self):
        async with self.lock:
            current_time = time.time()

            # Clean old calls from sliding window
            self._clean_call_history(current_time)

            # Check if we need to wait
            if len(self.call_history) >= self.max_calls - 2:  # Conservative buffer
                # Calculate wait time based on oldest call
                if self.call_history:
                    oldest_call_time = self.call_history[0]
                    wait_time = oldest_call_time + self.window_size - current_time + 0.1  # Small buffer

                    if wait_time > 0:
                        api_logger.warning(f"Rate limit approaching for {self.api_type}, waiting {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        # Clean again after waiting
                        self._clean_call_history(time.time())

            # Record this call attempt
            self.call_history.append(current_time)

    def _clean_call_history(self, current_time):
        """Remove calls older than the window"""
        while self.call_history and current_time - self.call_history[0] > self.window_size:
            self.call_history.popleft()

    async def _execute_call(self, func, *args, **kwargs):
        """Execute the actual API call and handle response"""
        data, headers = {}, {}
        runtime = -1000

        try:
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            runtime = end_time - start_time

            if isinstance(result, tuple) and len(result) == 2:
                data, headers = result
            else:
                data = result

            # Reset 429 counter on success
            self.consecutive_429s = 0

            return data

        except Exception as e:
            # Extract headers if available
            if hasattr(e, 'context'):
                headers = e.context.get('headers', {})
            elif hasattr(e, 'response') and hasattr(e.response, 'headers'):
                headers = dict(e.response.headers)

            raise e

        finally:
            if self.has_rate_limit:
                await self._update_rate_limit_info(headers, func, runtime)

    async def _update_rate_limit_info(self, headers, func, runtime):
        """Update rate limit information from response headers"""
        if not headers:
            return

        try:
            remaining = headers.get(self.rate_limit_field)
            reset_time = headers.get(self.reset_time_field)

            if remaining is not None:
                remaining = int(remaining)

                # If server reports very low remaining calls, add extra buffer
                if remaining <= 3:
                    api_logger.warning(f"Low rate limit remaining for {self.api_type}: {remaining}")
                    # Add some artificial delay to be extra safe
                    await asyncio.sleep(0.5)

            if remaining is not None and reset_time is not None:
                reset_seconds = float(reset_time)
                api_logger.info(f"Called {self.api_type}.{func.__name__} ({runtime:.2f}s): "
                                f"{remaining} calls remaining, reset time is {reset_seconds}")

        except (ValueError, TypeError) as e:
            api_logger.error(f"Failed to parse rate limit headers for {self.api_type}: {e}")

    def _is_rate_limit_error(self, exception):
        """Check if exception is a rate limit error"""
        if hasattr(exception, 'status') and exception.status == 429:
            return True
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            return exception.response.status_code == 429
        if '429' in str(exception) or 'rate limit' in str(exception).lower():
            return True
        return False

    async def _handle_429_error(self):
        """Handle rate limit errors with exponential backoff"""
        async with self.lock:
            self.consecutive_429s += 1
            self.last_429_time = time.time()

            # Clear call history to be safe
            self.call_history.clear()

            # Exponential backoff: 2^n seconds, max 60 seconds
            backoff_time = min(2 ** self.consecutive_429s, 60)

            api_logger.error(f"Hit 429 for {self.api_type} (attempt {self.consecutive_429s}), "
                             f"backing off for {backoff_time}s")

            await asyncio.sleep(backoff_time)

    async def get_rate_limit_status(self):
        """Get current rate limit status for monitoring"""
        async with self.lock:
            current_time = time.time()
            self._clean_call_history(current_time)

            return {
                'api_type': self.api_type,
                'calls_in_window': len(self.call_history),
                'max_calls': self.max_calls,
                'calls_remaining': max(0, self.max_calls - len(self.call_history)),
                'consecutive_429s': self.consecutive_429s,
                'window_resets_in': max(0, self.call_history[0] + self.window_size - current_time) if self.call_history else 0
            }


async def update_benchmark_scenario_list(url: str, path: str, session):
    """Gets S5 benchmark scenario list """
    now = datetime.now(timezone.utc).timestamp()
    if os.path.exists(path):
        if now - os.path.getmtime(path) < 86400:
            return None, None
    try:
        async with session.get(
                url=url
        ) as response:
            response.raise_for_status()
            headers = response.headers
            config = await response.json()
            categories = [
                {
                    "id": category["id"],
                    "subcategories": [{"id": sub["id"]} for sub in
                                      category["subcategories"]]
                } for category in config["categories"]
            ]
            tier_energies = [
                [
                    j['energy_threshold'] for j in config['ranks'] if j['tier_id'] == i
                ] for i in [2, 3, 4]
            ]
            novice_scenarios, intermediate_scenarios, advanced_scenarios = [[
                {
                    "thresholds": tier['thresholds'],
                    "subcategoryId": scenario['subcategory_id'],
                    "score": None,
                    "task_id": scenario.get('task_id', None),
                    "weapon_id": scenario.get('weapon_id', None)
                }
                for scenario in config["scenarios"]
                for tier in scenario["tiers"]
                if tier['tier_id'] == tier_number
            ] for tier_number in [2, 3, 4]]
            final_json = {
                "categories": categories,
                "tier_energies": tier_energies,
                "novice_scenarios": novice_scenarios,
                "intermediate_scenarios": intermediate_scenarios,
                "advanced_scenarios": advanced_scenarios
            }
            async with FILE_LOCK:
                async with aiofiles.open(
                        path, "w",
                        encoding="utf-8"
                ) as f:
                    await f.write(json.dumps(final_json,
                                             ensure_ascii=False, indent=4))
            return config, headers
    except Exception as e:
        raise ErrorFetchingData(f"Error while fetching scenario "
                                f"list for S5 benchmarks "
                                f"\n\nStatus code: {response.status}. {str(e)}")


async def get_json(response: aiohttp.ClientResponse):
    try:
        data = await response.json()
        return data
    except Exception as e:
        raise UnableToDecodeJson(" ")


async def setup(bot): pass
async def teardown(bot): pass
