import discord
from discord.ext import commands


class AssignRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    def assign_highest_roles(
            self, rank_leader, dm_leader, voltaic_leader, voltaic_val_leader
    ):
        pass
