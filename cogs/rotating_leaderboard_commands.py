import discord
from discord.ext import commands
from discord import app_commands
from utils.log import logger

from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel, is_correct_author


class CreateLeaderboardModal(discord.ui.View):
    pass


class RotatingLeaderboardsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @is_correct_author()
    @is_correct_channel()
    @app_commands.command(name="create_leaderboard",
                          description="Creates a new rotating leaderboard. "
                                      "Opens a modal to submit details")
    async def create_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_nick = interaction.user.display_name
        user_id = interaction.user.id


async def setup(bot):
    await bot.add_cog(RotatingLeaderboardsCommands(bot))
