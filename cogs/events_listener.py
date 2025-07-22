import discord
from discord.ext import commands
from services.db.guilds import initialize_guild, set_guild_inactive
from settings import OWNER_ID
from utils.log import logger


class EventListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # TODO: Implement logic for when the bot joins a guild
        owner = self.bot.get_user(OWNER_ID)
        await owner.send(f"I have joined a new guild: {guild.name} ({guild.id})")
        logger.info(f"Joined new guild: {guild.name} ({guild.id}), "
                    f"initializing...")
        await initialize_guild(self.bot.db, guild.id, guild.name)


    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # TODO: Implement logic for when the bot is removed from a guild
        await set_guild_inactive(self.bot.db, guild.id)


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
