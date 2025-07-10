import traceback
import discord
from discord.ext import commands
from discord import app_commands
from utils.checks import is_correct_channel, is_correct_author
from services.db.leaderboard_database import (
    get_valorant_rank_leaderboard_data,
    get_valorant_dm_leaderboard_data,
    get_voltaic_s5_benchmarks_leaderboard_data,
    get_voltaic_s1_val_benchmarks_leaderboard_data)
from settings import GUILD_ID, LEADERBOARD_TYPES
from utils.database_helper import (execute_commit,
                                   execute_fetch)
from utils.log import logger
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

eastern = ZoneInfo("America/New_York")

scheduler = AsyncIOScheduler(timezone=eastern)


class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo("America/New_York"))
        self.scheduler.add_job(
            self.weekly_task,
            CronTrigger(day_of_week="sun", hour=23, minute=59),
        )
        self.scheduler.start()

    @scheduler.scheduled_job(
        CronTrigger(day_of_week="sun", hour=23, minute=59, timezone=eastern)
    )
    async def weekly_task(self):
        logger.info("Running weekly task every Sunday at 11:59 PM Eastern")
        await self.update_weekly_roles()


    async def update_weekly_roles(self):
        guild = self.bot.get_guild(GUILD_ID)
        for leaderboard_type in LEADERBOARD_TYPES:
            if (leaderboard_type == "dojo_aimlabs_playlist_balanced" or
                    leaderboard_type == "dojo_aimlabs_playlist_advanced"):
                continue

            # Get top scorer for that week
            winner_id = await self.get_top_scorer_from_db(leaderboard_type)
            if not winner_id:
                logger.error(f"Winner ID for {leaderboard_type} not found, skipping...")
                continue

            # Fetch winner + last winner
            winner = guild.get_member(winner_id)
            last_winner_id = await self.get_last_winner(leaderboard_type)
            last_winner = guild.get_member(last_winner_id) if last_winner_id else None

            role = discord.utils.get(guild.roles, id=self.get_role_from_lb_type(leaderboard_type))

            if not role:
                logger.error(f"Role for {leaderboard_type} not found.")
                continue

            # Remove role from old winner
            if last_winner and role in last_winner.roles:
                await last_winner.remove_roles(role)

            # Assign role to new winner
            if winner and role not in winner.roles:
                await winner.add_roles(role)

            # Save this new winner to the DB
            await self.insert_weekly_winner(leaderboard_type, winner_id)


    @staticmethod
    def get_role_from_lb_type(lb_type):
        # TODO: Fix hardcoded values for roles
        match lb_type:
            case "valorant_rank_leaderboard":
                role_id = 1392632876931088487
            case "valorant_dm_leaderboard":
                role_id = 1392631799783358594
            case "voltaic_S5_benchmarks_leaderboard":
                role_id = 1392633052886339584
            case "voltaic_S1_valorant_benchmarks_leaderboard":
                role_id = 1392633052886339584
            case _:
                role_id = None
        return role_id


    @staticmethod
    async def get_top_scorer_from_db(lb_type):
        match lb_type:
            case "valorant_rank_leaderboard":
                fetched_data = await get_valorant_rank_leaderboard_data()
            case "valorant_dm_leaderboard":
                fetched_data = await get_valorant_dm_leaderboard_data()
            case "voltaic_S5_benchmarks_leaderboard":
                fetched_data = await get_voltaic_s5_benchmarks_leaderboard_data()
            case "voltaic_S1_valorant_benchmarks_leaderboard":
                fetched_data = await get_voltaic_s1_val_benchmarks_leaderboard_data()
            case _:
                fetched_data = None
        return fetched_data[0]


    @staticmethod
    async def get_last_winner(lb_type):
        sql_statement = """
        SELECT discord_id FROM weekly_leaderboard_winners
        WHERE leaderboard_type = ?
        """
        await execute_fetch(
            sql_statement,
            (lb_type,),
            "weekly_leaderboard_winners"
        )


    @staticmethod
    async def insert_weekly_winner(lb_type, discord_id):
        sql_statement = """
        INSERT INTO weekly_leaderboard_winners (leaderboard_type, discord_id)
        VALUES (?, ?)
        ON CONFLICT (leaderboard_type) DO UPDATE SET
            discord_id = excluded.discord_id
        """
        await execute_commit(
            sql_statement,
            (lb_type, discord_id),
            "weekly_leaderboard_winners",
            "UPSERT"
        )


    @@app_commands.command(name="assign_winner_role",
                           description="Manually assign winner role.")
    @is_correct_author()
    @is_correct_channel()
    async def assign_winner_role(self, interaction: discord.Interaction,
                                 discord_member: discord.Member,
                                 discord_role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.nick or interaction.user.name
        user_id = interaction.user.id
        try:
            await discord_member.add_roles(discord_role)
            logger.info(f"{user_nick} ({user_id}) "
                        f"assigned {discord_role.name} role to "
                        f"{discord_member.nick or discord_member.name}.")
            await interaction.followup.send(f"Successfully assigned "
                                            f"`{discord_role.name}` role to "
                                            f"`{discord_member.name}`")
        except discord.Forbidden:
            logger.error(f"Forbidden for {discord_member.display_name}")
            await interaction.followup.send(f"Forbidden: No permissions to "
                                            f"assign role "
                                            f"`{discord_role.name}`")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_leaderboard "
                f"-> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")

def setup(bot):
    bot.add_cog(RoleManager(bot))
def teardown(bot): pass
