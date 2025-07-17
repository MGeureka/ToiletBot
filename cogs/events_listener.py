import discord
from discord.ext import commands


class EventListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # TODO: Implement logic for when the bot joins a guild
        ...


    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # TODO: Implement logic for when the bot is removed from a guild
        ...


    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member,
                               after: discord.Member):
        # TODO: Implement logic for when a member's status or roles change
        ...


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # TODO: Implement logic for when a member leaves the guild
        ...


async def setup(bot):
    await bot.add_cog(EventListener(bot))
async def teardown(bot): pass
