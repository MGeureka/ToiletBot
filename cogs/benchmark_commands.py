import discord
from discord.ext import commands
from discord import app_commands
from utils.log import logger

# from services.api.kovaaks_api import
from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel

class BenchmarkCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="s5_benchmarks", description="Get your kovaaks s5 "
                                                            "benchmarks")
    async def s5_benchmarks(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_nick = interaction.user.display_name
        user_id = interaction.user.id


# def setup(bot):
#     await bot.add_cog(BenchmarkCommands(bot))
