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
from settings import GUILD_ID, LEADERBOARD_TYPES, DOJO_RANK_ROLES
from utils.database_helper import (execute_commit,
                                   execute_fetch)
from utils.log import logger
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
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
        # Valorant rank role update every 20 minutes
        self.scheduler.add_job(
            self.assign_rank_roles,
            IntervalTrigger(minutes=20),
        )
        self.scheduler.start()
        logger.info("Started scheduler")


    def cog_unload(self):
        self.scheduler.shutdown()


    async def weekly_task(self):
        logger.info("Running weekly task every Sunday at 11:59 PM Eastern")
        await self.update_weekly_roles()


    async def update_weekly_roles(self):
        guild = self.bot.get_guild(GUILD_ID)
        for leaderboard_type in LEADERBOARD_TYPES:
            if (leaderboard_type == "dojo_aimlabs_playlist_balanced" or
                    leaderboard_type == "dojo_aimlabs_playlist_advanced" or
                    leaderboard_type == "voltaic_S5_benchmarks_leaderboard" or
                    leaderboard_type == "voltaic_S1_valorant_benchmarks_leaderboard"):
                continue
            # Get top scorer for that week
            raw_winner_id = await self.get_top_scorer_from_db(leaderboard_type)
            winner_id = raw_winner_id[0]
            logger.info(f"Found top scorer from this week, id: {winner_id}")
            if not winner_id:
                logger.error(f"Winner ID for {leaderboard_type} not found, skipping...")
                continue

            # Fetch winner + last winner
            winner = guild.get_member(winner_id)
            last_winner_id = await self.get_last_winner(leaderboard_type)
            logger.info(f"Found top scorer from last week, id: {last_winner_id}")
            last_winner = guild.get_member(last_winner_id) if last_winner_id else None

            role_id = self.get_role_from_lb_type(leaderboard_type)
            if not role_id:
                logger.error(f"Role ID for {leaderboard_type} not found, skipping...")
                continue
            role = discord.utils.get(guild.roles, id=role_id)
            logger.info(f"Found corresponding role {role.name}")
            if not role:
                logger.error(f"Role for {leaderboard_type} not found.")
                continue

            # Remove role from old winner
            if last_winner and role in last_winner.roles:
                logger.info(f"Removed {role.name} for {leaderboard_type} from {last_winner.nick or last_winner.name}")
                await last_winner.remove_roles(role)

            # Assign role to new winner
            if winner and role not in winner.roles:
                logger.info(f"Assigned {role.name} for {leaderboard_type} to {winner.nick or winner.name}")
                await winner.add_roles(role)

            # Save this new winner to the DB
            await self.insert_weekly_winner(leaderboard_type, winner_id)


    async def assign_rank_roles(self):
        guild = self.bot.get_guild(GUILD_ID)
        data = await get_valorant_rank_leaderboard_data()
        for profile in data:
            (discord_id, discord_username, current_rank,
             current_rank_id, current_rr) = profile

            member = guild.get_member(discord_id)

            if not member:
                logger.warning(f"Member with ID {discord_id} not found in guild.")
                continue

            role_id = DOJO_RANK_ROLES.get(current_rank_id)

            if not role_id:
                continue  # Unknown rank ID

            current_role = discord.utils.get(member.roles, id=role_id)
            if current_role:
                continue
            roles_to_remove = [discord.utils.get(guild.roles, id=rid)
                               for rid in DOJO_RANK_ROLES.values()]
            roles_to_remove = [role for role in roles_to_remove if role in member.roles]
            if roles_to_remove:
                logger.info(f"Removing roles {', '.join(role.name for role in roles_to_remove)} "
                            f"from {member.nick or member.name}")
                # await member.remove_roles(*roles_to_remove)
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                logger.info(f"Assigning role {role.name} to {member.nick or member.name}")
                # await member.add_roles(role)


    @staticmethod
    def get_role_from_lb_type(lb_type):
        # TODO: Fix hardcoded values for roles
        match lb_type:
            case "valorant_rank_leaderboard":
                role_id = 1392632876931088487
            case "valorant_dm_leaderboard":
                role_id = 1392631799783358594
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
        if fetched_data and len(fetched_data) > 0:
            return fetched_data[0]
        return None


    @staticmethod
    async def get_last_winner(lb_type):
        sql_statement = """
        SELECT discord_id FROM weekly_leaderboard_winners
        WHERE leaderboard_type = ?
        """
        data = await execute_fetch(
            sql_statement,
            (lb_type,),
            "weekly_leaderboard_winners"
        )
        if data and len(data) > 0:
            return data[0][0]
        return None


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


    @app_commands.command(name="assign_winner_role",
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


async def setup(bot):
    await bot.add_cog(RoleManager(bot))
async def teardown(bot): pass
