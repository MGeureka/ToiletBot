import discord
from discord.ext import commands
from discord import app_commands
from utils.database_helper import execute_commit, execute_fetch
from utils.log import logger
import traceback
from datetime import datetime, timezone
from utils.checks import is_correct_author


@app_commands.guilds(1333243573440741458)
class DojoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ddc_signup", description="Sign up for the Dopai Dojo Cup")
    @app_commands.choices(role1=[
        app_commands.Choice(name="Initiator", value="Initiator"),
        app_commands.Choice(name="Duelist", value="Duelist"),
        app_commands.Choice(name="Controller", value="Controller"),
        app_commands.Choice(name="Sentinel", value="Sentinel")
    ])
    @app_commands.choices(role2=[
        app_commands.Choice(name="Initiator", value="Initiator"),
        app_commands.Choice(name="Duelist", value="Duelist"),
        app_commands.Choice(name="Controller", value="Controller"),
        app_commands.Choice(name="Sentinel", value="Sentinel")
    ])
    async def ddc_signup(
            self, interaction: discord.Interaction, role1: str, role2: str
):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        user_nick = interaction.user.nick or interaction.user.display_name
        try:
            query = """
            INSERT INTO ddc_signup (discord_id, discord_username, roles, date_added)
            VALUES(?, ?, ?, ?)
            ON CONFLICT (discord_id) DO UPDATE
            SET discord_username = EXCLUDED.discord_username,
                roles = EXCLUDED.roles;
            """
            now = datetime.now(timezone.utc).isoformat()
            roles = f"{role1}, {role2}"
            values = (user_id, user_nick, roles, now)
            await execute_commit(query, values, table_name="ddc_signups", operation="UPSERT")
            await interaction.followup.send("You have successfully signed up")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/ddc_signup -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="ddc_opt_out", description="Opt out for the Dopai Dojo Cup")
    async def ddc_opt_out(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        user_nick = interaction.user.nick or interaction.user.display_name
        try:
            query = """
            DELETE FROM ddc_signup WHERE discord_id = ?;
            """
            values = (user_id,)
            await execute_commit(query, values, table_name="ddc_signups", operation="DELETE")
            await interaction.followup.send("You have successfully opted out of the DDC")
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/ddc_opt_out -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


async def setup(bot):
    await bot.add_cog(DojoCommands(bot))
async def teardown(bot): pass
