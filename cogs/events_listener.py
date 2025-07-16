import discord
from discord.ext import commands


class EventListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # @commands.Cog.listener()
    # async def on_interaction(self, interaction: discord.Interaction):
    #     """Global listener for all interactions"""
    #     user_nick = interaction.user.display_name
    #     user_id = interaction.user.id
    #     guild_name = interaction.guild.name
    #     guild_id = interaction.guild_id
    #     if interaction.command:
    #         print(f"{interaction.command.name} Interaction received from User: "
    #               f"{user_nick} ({user_id}) in Guild: {guild_name} "
    #               f"({guild_id}) in Channel: "
    #               f"{interaction.channel.name} ({interaction.channel_id}) "
    #               f"with args: {vars(interaction.namespace)}")
    #         if interaction.command_failed:
    #             print(f"{interaction.command.name} Interaction failed from "
    #                   f"User: {user_nick} ({user_id}) in Guild: {guild_name} "
    #                   f"({guild_id}) in Channel: "
    #                   f"{interaction.channel.name} ({interaction.channel_id}) "
    #                   f"with args: {vars(interaction.namespace)}")


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
