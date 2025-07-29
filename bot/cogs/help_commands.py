from discord import app_commands
from discord.ext import commands
from discord import Embed
import discord
from common.log import logger
from utils.checks import is_correct_channel
from utils.errors import CheckError
import traceback


class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List all available slash commands")
    @is_correct_channel()
    async def help(self, interaction: discord.Interaction):
        embed = Embed(title="List of Commands for Toilet Bot", color=discord.Color.blurple())
        file = discord.File("assets/images/toilet-pfp-fan-art.jpg", filename="help_thumbnail.jpg")
        embed.set_thumbnail(url="attachment://help_thumbnail.jpg")

        user_nick = interaction.user.nick or interaction.user.name
        user_id = interaction.user.id

        for command in self.bot.tree.get_commands():
            embed.add_field(name=f"`/{command.name}`", value=command.description or "N/A", inline=False)

        logger.info(f"{user_nick} ({user_id}) used {interaction.command.name}")
        await interaction.response.send_message(embed=embed, ephemeral=True, file=file)


    async def cog_app_command_error(self, interaction: discord.Interaction, e: app_commands.AppCommandError) -> None:
        if isinstance(e, CheckError):
            logger.warning(f"{interaction.user.nick or interaction.user.name} "
                           f"({interaction.user.id}) used {interaction.command.name} -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.response.send_message(e.message, ephemeral=True)
            return
        else:
            logger.error(
                f"{interaction.user.nick or interaction.user.name} ({interaction.user.id}) ran {interaction.command.name} -> Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.response.send_message(f"Ran into an unexpected error (oopsie teehee).\n\n{str(e)}", ehemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
