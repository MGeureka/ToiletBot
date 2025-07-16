import discord
from discord.ext import commands


class EventListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Global listener for all interactions"""
        user_nick = interaction.user.display_name
        user_id = interaction.user.id

        if interaction.command:
            print(f"{interaction.command.namespace} Interaction received from "
                  f"{user_nick} ({user_id}) in channel "
                  f"{interaction.channel.name} ({interaction.channel_id})")
            if interaction.command_failed:
                print(f"Interaction command {interaction.command.name} "
                      f"failed for {user_nick} ({user_id}) in channel "
                      f"{interaction.channel.name} ({interaction.channel_id})")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        ...


async def setup(bot):
    await bot.add_cog(EventListener(bot))
async def teardown(bot): pass
