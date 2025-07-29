import os.path

from common.log import logger
import time
from datetime import datetime, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from PIL import Image
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks

from services.db.discord_database import update_discord_profile
from writer.leaderboard_database import (
    update_valorant_rank_leaderboard,
    update_valorant_dm_leaderboard,
    update_voltaic_s5_leaderboard,
    update_voltaic_val_s1_leaderboard,
    update_dojo_aimlabs_balanced_playlist_leaderboard,
    update_dojo_aimlabs_advanced_playlist_leaderboard,
    get_valorant_rank_leaderboard_data,
    get_valorant_dm_leaderboard_data,
    get_voltaic_s5_benchmarks_leaderboard_data,
    get_voltaic_s1_val_benchmarks_leaderboard_data,
    get_dojo_aimlabs_playlist_balanced_leaderboard_data,
    get_dojo_aimlabs_playlist_advanced_leaderboard_data
)
from utils.database_helper import (get_profile_from_db, get_discord_profiles,
                                       set_profile_inactive)
from utils.errors import CheckError
from utils.image_gen import LeaderboardRenderer, delete_files_indir
import traceback
from utils.checks import is_correct_channel, is_correct_author
from settings import (LEADERBOARD_TYPES, AVATAR_CACHE_DIR, LEADERBOARD_CACHE_DIR,
                          LEADERBOARD_CACHE_LOCK, AVATAR_CACHE_LOCK, GUILD_ID)
from configs.leaderboard_config import leaderboard_types_list

LEADERBOARD_UPDATE_METHODS = {
    leaderboard_types_list[0]: update_valorant_rank_leaderboard,
    leaderboard_types_list[1]: update_valorant_dm_leaderboard,
    leaderboard_types_list[2]: update_voltaic_s5_leaderboard,
    leaderboard_types_list[3]: update_voltaic_val_s1_leaderboard,
    leaderboard_types_list[4]: update_dojo_aimlabs_balanced_playlist_leaderboard,
    leaderboard_types_list[5]: update_dojo_aimlabs_advanced_playlist_leaderboard
}

LEADERBOARD_RENDERER = {
    leaderboard_types_list[0]: LeaderboardRenderer(leaderboard_types_list[0]),
    leaderboard_types_list[1]: LeaderboardRenderer(leaderboard_types_list[1]),
    leaderboard_types_list[2]: LeaderboardRenderer(leaderboard_types_list[2]),
    leaderboard_types_list[3]: LeaderboardRenderer(leaderboard_types_list[3]),
    leaderboard_types_list[4]: LeaderboardRenderer(leaderboard_types_list[4]),
    leaderboard_types_list[5]: LeaderboardRenderer(leaderboard_types_list[5])
}

DEFAULT_ROLE = 1333353367896068146


class DatabaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_updated_time = None
        self.updating = False


    @app_commands.command(name="start_leaderboard_updates",
                          description="Starts the background loop which updates the database every 10 minutes")
    @is_correct_author()
    @is_correct_channel()
    async def start_leaderboard_updates(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        try:
            if self.refresh_leaderboards.is_running():
                await interaction.followup.send(f"Background loop updates is already running.")
                return

            logger.info(f"{user_nick} ({user_id}) ran /start_leaderboard_updates. Starting background loop updates")
            self.refresh_leaderboards.start()
            await interaction.followup.send(f"Successfully started background loop updates")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_leaderboard "
                f"-> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="stop_leaderboard_updates",
                          description="Stops the background loop which updates the database every 10 minutes")
    @is_correct_author()
    @is_correct_channel()
    async def stop_leaderboard_updates(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        try:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/stop_leaderboard_updates. "
                           f"Stopping background loop updates")
            self.refresh_leaderboards.cancel()
            await interaction.followup.send(f"Successfully "
                                            f"stopped background loop updates")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_leaderboard with "
                f"username -> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    async def refresh_one_leaderboard(self, leaderboard_type: str):
        logger.info(f"Updating {leaderboard_type} leaderboard...")
        logger.info(f"Regenerating {leaderboard_type} leaderboard images...")
        start_time = time.time()
        await self.regenerate_discord_leaderboard_images([leaderboard_type])
        end_time = time.time()
        logger.info(f"Done regenerating {leaderboard_type} leaderboard in "
                    f"{end_time - start_time:.2f} s.")


    @tasks.loop(minutes=3)
    async def refresh_leaderboards(self):
        try:
            logger.info("Updating all leaderboards...")
            start_time = time.time()
            await asyncio.gather(self.regenerate_discord_leaderboard_images(
                LEADERBOARD_TYPES),
                                 self.regenerate_discord_user_avatar())
            end_time = time.time()
            logger.info(f"Done regenerating all leaderboard images in "
                        f"{end_time - start_time:.2f} s")
            self.last_updated_time = datetime.now(timezone.utc).timestamp()
            leaderboard_cog = self.bot.get_cog("LeaderboardCommands")
            await leaderboard_cog.view.update_leaderboard_message()
            self.updating = False
        except Exception as e:
            logger.error(
                f"Ran into an error while updating leaderboards -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )


    @refresh_leaderboards.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


    async def get_last_updated_time(self) -> float | None:
        return self.last_updated_time


    @app_commands.command(name="get_my_profiles",
                          description="Get your active profiles")
    @is_correct_channel()
    async def get_user_profiles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        profile_cnt = 0
        try:
            valorant_profile, aimlabs_profile, kovaaks_profile = \
                await asyncio.gather(
                    get_profile_from_db(
                        self.bot.db, user_id, guild_id, profile="val"
                    ),
                    get_profile_from_db(
                        self.bot.db, user_id, guild_id, profile="aimlabs"
                    ),
                    get_profile_from_db(
                        self.bot.db, user_id, guild_id, profile="kovaaks"
                    )
                )
            logger.info(f"{user_nick} ({user_id}) in guild {guild_id} ran "
                        f"/get_user_profiles successfully.")
            message = f"`{user_nick}` has profiles for:"
            if valorant_profile and valorant_profile['is_active']:
                message += (f"\nValorant: "
                            f"`{valorant_profile['valorant_username']}#"
                            f"{valorant_profile['valorant_tag']}` ")
                profile_cnt += 1
            if aimlabs_profile and aimlabs_profile['is_active']:
                message += f"\nAimlabs: `{aimlabs_profile['aimlabs_username']}`"
                profile_cnt += 1
            if kovaaks_profile and kovaaks_profile['is_active']:
                message += f"\nKovaaks: `{kovaaks_profile['kovaaks_username']}`"
                profile_cnt += 1
            if profile_cnt > 0:
                await interaction.followup.send(message)
            else:
                await interaction.followup.send(f"No profiles found for "
                                                f"`{user_nick}`")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/get_my_profiles -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="get_update_status",
                          description="Get the status of the update cycle")
    @is_correct_channel()
    async def get_update_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        try:
            message = None
            message_string = (f"Leaderboards are currently being updated. "
                              f"Please wait.")
            while self.updating:
                if message:
                    await message.edit(content=message_string)
                else:
                    await interaction.followup.send(message_string)
                    message = await interaction.original_response()
                await asyncio.sleep(2)

            if self.refresh_leaderboards.is_running():
                dt_plus_10 = self.last_updated_time + 10 * 60 # add 10 minutes
                dt_string = (f"Last updated leaderboards at "
                             f"<t:{round(self.last_updated_time)}:f>. "
                             f"Updating <t:{round(dt_plus_10)}:R>")
                if message:
                    await message.edit(content=dt_string)
                else:
                    await interaction.followup.send(dt_string)
            else:
                await interaction.followup.send(f"Not updating leaderboards "
                                                f"currently.")
            logger.info(f"{user_nick} ({user_id}) ran /get_update_status "
                        f"successfully.")

        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /get_update_status with "
                f"username -> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @staticmethod
    async def get_data(selected_value):
        match selected_value:
            case "valorant_rank_leaderboard":
                return await get_valorant_rank_leaderboard_data()
            case "valorant_dm_leaderboard":
                return await get_valorant_dm_leaderboard_data()
            case "voltaic_S5_benchmarks_leaderboard":
                return await get_voltaic_s5_benchmarks_leaderboard_data()
            case "voltaic_S1_valorant_benchmarks_leaderboard":
                return await get_voltaic_s1_val_benchmarks_leaderboard_data()
            case "dojo_aimlabs_playlist_balanced":
                return await get_dojo_aimlabs_playlist_balanced_leaderboard_data()
            case "dojo_aimlabs_playlist_advanced":
                return await get_dojo_aimlabs_playlist_advanced_leaderboard_data()
            case "discord_profiles":
                return await get_discord_profiles()
            case _:
                return None


    @app_commands.command(name="regen_images", description="Show leaderboards")
    @is_correct_author()
    @is_correct_channel()
    async def regen_images(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.nick or interaction.user.name
        user_id = interaction.user.id
        try:
            await self.regenerate_discord_leaderboard_images(LEADERBOARD_TYPES)
            logger.info(f"{user_nick} ({user_id}) used /regen_images")
            await interaction.followup.send(f"Success")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_leaderboard with "
                f"username -> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    async def regenerate_discord_user_avatar(self):
        data = await self.get_data("discord_profiles")
        guild = self.bot.get_guild(GUILD_ID)
        now = datetime.now(timezone.utc).timestamp()
        async def process_avatar(user_id, discord_username):
            path = AVATAR_CACHE_DIR / f"{user_id}.jpeg"
            if os.path.exists(path):
                if now - os.path.getmtime(path) < 86400:
                    return
            try:
                user = guild.get_member(user_id) or await guild.fetch_member(user_id)
                if user is None:
                    logger.error(f"Failed to get user "
                                 f"{discord_username} ({user_id})")
                    await set_profile_inactive(user_id)
                    logger.info(f"Set Profile "
                                f"{discord_username} ({user_id}) to inactive")
                    return
                has_role = user.get_role(DEFAULT_ROLE)
                if not has_role:
                    await set_profile_inactive(user_id)
                    logger.info(f"Set Profile "
                                f"{discord_username} ({user_id}) to inactive")
                    return
                user_nick = user.nick or user.display_name
                asset = user.display_avatar or user.default_avatar
                await update_discord_profile(user_nick, user_id)
                avatar_bytes = await asset.read()
                avatar = Image.open(BytesIO(avatar_bytes))
                avatar = avatar.resize((100, 100))
                avatar = avatar.convert("RGB")
                with AVATAR_CACHE_LOCK:
                    avatar.save(path)
            except discord.NotFound as e:
                logger.info(f"Failed to find {discord_username} ({user_id}) "
                            f"in guild, setting to inactive in database")
                await set_profile_inactive(user_id)
            except Exception as e:
                logger.error(f"Error updating avatar/username for "
                             f"{discord_username} ({user_id}): "
                             f"{str(e)}")
                return

        await asyncio.gather(*[process_avatar(profile[0], profile[1]) for profile in data])


    async def regenerate_discord_leaderboard_images(self,
                                                    leaderboard_list: list):
        executor = ThreadPoolExecutor(max_workers=4)
        leaderboard_page_size = 10
        image_tasks = []
        for leaderboard_type in leaderboard_list:
            data = await self.get_data(leaderboard_type)
            total_pages = max(1, ((len(data) + leaderboard_page_size - 1) //
                                  leaderboard_page_size))
            async with LEADERBOARD_CACHE_LOCK:
                await delete_files_indir(LEADERBOARD_CACHE_DIR /
                                         leaderboard_type)
            for current_page in range(1, total_pages + 1):
                start_idx = (current_page - 1) * leaderboard_page_size
                end_idx = min(start_idx + leaderboard_page_size, len(data))
                page_data = data[start_idx:end_idx]
                image_tasks.append(self._generate_and_save_image(
                    leaderboard_type, page_data, current_page,
                    total_pages, start_idx, executor))


        await asyncio.gather(*image_tasks)


    @staticmethod
    async def _generate_and_save_image(leaderboard_type, page_data,
                                       current_page, total_pages, start_idx,
                                       executor):
        try:
            ld_renderer = LEADERBOARD_RENDERER[leaderboard_type]
            image = await asyncio.get_event_loop().run_in_executor(
                executor, ld_renderer.get_image, page_data, current_page,
                total_pages, start_idx)
            async with LEADERBOARD_CACHE_LOCK:
                image.save(LEADERBOARD_CACHE_DIR / f"{leaderboard_type}/"
                                                   f"{current_page}.jpeg",
                           optimize=True, quality=50)
        except Exception as e:
            raise e


    async def cog_app_command_error(self, interaction: discord.Interaction,
                                    e: app_commands.AppCommandError) -> None:
        if isinstance(e, CheckError):
            logger.warning(f"{interaction.user.display_name} "
                           f"({interaction.user.id}) used "
                           f"{interaction.command.name} ->"
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.response.send_message(e.message, ephemeral=True)
            return


    async def cog_unload(self):
        self.refresh_leaderboards.cancel()


async def setup(bot):
    cog = DatabaseCommands(bot)
    await bot.add_cog(cog)

    if cog.refresh_leaderboards.is_running():
        cog.refresh_leaderboards.restart()
    else:
        cog.refresh_leaderboards.start()
