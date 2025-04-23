from configs import log_config

logger = log_config.logging.getLogger("bot")
api_logger = log_config.logging.getLogger("api")
from datetime import datetime, timezone
import json


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def log_transaction(
        db,
        transaction_id: str,
        operation: str,
        table_name: str,
        query: str,
        parameters: tuple | list,
        status: str,
        error_message: str = None,
        affected_rows: int = 0
):
    timestamp = datetime.now(timezone.utc).isoformat()
    parameters_json = json.dumps(parameters, cls=DateTimeEncoder)

    log_query = '''
    INSERT INTO transaction_logs 
    (timestamp, operation, table_name, query, parameters, status, error_message, affected_rows, transaction_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    log_values = (
        timestamp, operation, table_name, query, parameters_json,
        status, error_message, affected_rows, transaction_id
    )

    await db.execute(log_query, log_values)
    await db.commit()


async def setup(bot): pass
async def teardown(bot): pass
