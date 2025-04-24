import traceback

import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import Select, View

from datetime import datetime, timezone
from utils.database_helper import (get_leaderboard_message_state,
                                   update_leaderboard_message_state)
from settings import (LEADERBOARD_TYPES, LEADERBOARD_CACHE_DIR,
                      LEADERBOARD_CACHE_LOCK, LEADERBOARD_CHANNEL_ID)
from utils.checks import is_correct_author, is_correct_channel
from utils.errors import CheckError
from utils.log import logger
from pathlib import Path
import asyncio


class LeaderboardView(View):
    def __init__(self, bot):
        try:
            super().__init__(timeout=None)  # No timeout for persistent view
            self.bot = bot
            self.current_page = 1
            self.sep = 10
            # Create the dropdown menu
            self.add_item(LeaderboardSelect(self))
            self.leaderboard_type = "valorant_rank_leaderboard"
            self.path = LEADERBOARD_CACHE_DIR / self.leaderboard_type
            self.total_pages = len(
                [f for f in Path(self.path).iterdir() if f.is_file()]
            )
            self.channel = None
            self.message_id = None
            self.message = None
            self.img_file = None
            self._refreshing_leaderboard = False
            self._debounce_task: asyncio.Task | None = None

        except Exception as e:
            logger.error(f"{str(e)}\n{traceback.format_exc()}")


    async def debounce_update(self, delay=0.5):
        if self._debounce_task:
            self._debounce_task.cancel()


        async def do_update():
            await asyncio.sleep(delay)
            await self.update_leaderboard_message()

        self._debounce_task = asyncio.create_task(do_update())


    async def initialize_messages(self):
        self.channel = await self.bot.fetch_channel(LEADERBOARD_CHANNEL_ID)
        try:
            self.message_id = await get_leaderboard_message_state()
            if self.message_id:
                self.message = await self.channel.fetch_message(self.message_id)
                logger.info(f"Found persistent leaderboard with "
                            f"message id {self.message_id}")
            else:
                self.message = None
        except Exception as e:
            logger.error(f"{str(e)}\n{traceback.format_exc()}")


    @tasks.loop(seconds=30)
    async def keep_on_top(self):
        last_message = [message async for message in
                        self.channel.history(limit=1)][0]
        if last_message.id != self.message_id:
            await self.message.delete()
            self.message_id = None
            self.message = None
            await self.update_leaderboard_message()


    async def update_leaderboard_message(self):
        # await self.bot.wait_until_ready()
        try:
            async with LEADERBOARD_CACHE_LOCK:
                filename = f"{self.current_page}.jpeg"
                file_path = self.path / filename
                if not file_path.exists():
                    return
                self.img_file = discord.File(file_path, filename=filename)
            db_commands = self.bot.get_cog("DatabaseCommands")
            time = await db_commands.get_last_updated_time()
            if time is None:
                time = datetime.now(timezone.utc).timestamp()
            self.update_buttons()
            last_updated = f"Last updated: <t:{round(time)}:F>"
            if self.message:
                await self.message.edit(content=last_updated,
                                        attachments=[self.img_file],
                                        view=self)
            else:
                # If no original response exists, send a new message
                self.message = await self.channel.send(content=last_updated,
                                                       file=self.img_file,
                                                       view=self)
                self.message_id = self.message.id
                await update_leaderboard_message_state(self.message_id)
        except discord.errors.HTTPException as e:
            logger.error(f"Ran into HTTP exception: "
                         f"{str(e)}\n{traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Error occurred while updating the leaderboard message"
                         f": {str(e)}\n{traceback.format_exc()}")

    def update_buttons(self):
        try:
            if self.current_page == 1:
                self.first_page_button.disabled = True
                self.prev_button.disabled = True
                self.first_page_button.style = discord.ButtonStyle.gray
                self.prev_button.style = discord.ButtonStyle.gray
            else:
                self.first_page_button.disabled = False
                self.prev_button.disabled = False
                self.first_page_button.style = discord.ButtonStyle.green
                self.prev_button.style = discord.ButtonStyle.primary

            if self.current_page >= self.total_pages:
                self.next_button.disabled = True
                self.last_page_button.disabled = True
                self.last_page_button.style = discord.ButtonStyle.gray
                self.next_button.style = discord.ButtonStyle.gray
            else:
                self.next_button.disabled = False
                self.last_page_button.disabled = False
                self.last_page_button.style = discord.ButtonStyle.green
                self.next_button.style = discord.ButtonStyle.primary
        except Exception as e:
            logger.error(f"Error when updating buttons: "
                         f"{str(e)}\n{traceback.format_exc()}")

    @discord.ui.button(label="|<",
                       style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_leaderboard_message()

    @discord.ui.button(label="<",
                       style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.debounce_update()

    @discord.ui.button(label="↻",
                       style=discord.ButtonStyle.primary)
    async def reload_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_nick = interaction.user.display_name
        user_id = interaction.user.id

        if button.disabled or self._refreshing_leaderboard:
            logger.warning(f"{user_nick} ({user_id}) refreshed lb on cooldown")
            return


        self._refreshing_leaderboard = True
        button.label = "⏳"
        await self.update_leaderboard_message()
        try:
            db_commands = self.bot.get_cog("DatabaseCommands")
            logger.info(f"{user_nick} ({user_id}) refreshed leaderboard "
                        f"{self.leaderboard_type}")
            await db_commands.refresh_one_leaderboard(self.leaderboard_type)
            await asyncio.sleep(2)
            button.label = "✔"
            await self.update_leaderboard_message()
            await asyncio.sleep(3)
            button.label = "↻"
            button.disabled = True
            await self.update_leaderboard_message()
            self._refreshing_leaderboard = False
        except Exception as e:
            logger.error(f"{str(e)}\n{traceback.format_exc()}")
            button.label = "❌"
            await self.update_leaderboard_message()
            logger.info(f"{user_nick} ({user_id}) refreshed leaderboard -> "
                        f"Caused error: {str(e)}/n{traceback.format_exc()}")
            await asyncio.sleep(3)
            button.label = "↻"
            button.disabled = True
            await self.update_leaderboard_message()
            self._refreshing_leaderboard = False
        finally:
            await asyncio.sleep(30)
            button.disabled = False
            await self.update_leaderboard_message()


    @discord.ui.button(label=">",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.debounce_update()

    @discord.ui.button(label=">|",
                       style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = self.total_pages
        await self.update_leaderboard_message()


    async def on_error(self, interaction: discord.Interaction, error,
                       item: discord.ui.Item):
        logger.error(f"Error in LeaderboardView when {item} was used"
                     f"{str(error)}/n{traceback.format_exc()}")


class LeaderboardSelect(Select):
    def __init__(self, leaderboard_view):
        self.leaderboard_view = leaderboard_view
        # Define options for different leaderboard types
        options = [discord.SelectOption(label=value[0], value=key, description=value[1])
                   for key, value in LEADERBOARD_TYPES.items()]

        super().__init__(placeholder="Select leaderboard type...",
                         options=options, row=1)


    async def callback(self, interaction: discord.Interaction):
        # Get the selected option
        try:
            await interaction.response.defer()
            selected_type = self.values[0]
            self.leaderboard_view.leaderboard_type = selected_type
            self.leaderboard_view.current_page = 1
            self.leaderboard_view.path = LEADERBOARD_CACHE_DIR / selected_type
            self.leaderboard_view.total_pages = len(
                [f for f in Path(self.leaderboard_view.path).iterdir() if f.is_file()]
            )
            await self.leaderboard_view.update_leaderboard_message()
        except Exception as e:
            logger.error(f"Error changing leaderboard type: "
                         f"{str(e)}\n{traceback.format_exc()}")


class LeaderboardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.view = LeaderboardView(self.bot)


    async def cog_app_command_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError) -> None:
        if isinstance(e, CheckError):
            logger.warning(f"{interaction.user.display_name} "
                           f"({interaction.user.id}) used "
                           f"{interaction.command.name} -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.response.send_message(e.message, ephemeral=True)
            return


    async def cog_unload(self):
        self.view.keep_on_top.cancel()


async def setup(bot):
    cog = LeaderboardCommands(bot)
    await bot.add_cog(cog)

    await cog.view.initialize_messages()
    await cog.view.update_leaderboard_message()

    if cog.view.keep_on_top.is_running():
        cog.view.keep_on_top.restart()
    else:
        cog.view.keep_on_top.start()

async def teardown(bot):pass
