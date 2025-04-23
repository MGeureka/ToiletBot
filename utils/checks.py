import discord
from settings import VERIFIED_USERS, LEADERBOARD_CHANNEL_ID
from utils.errors import UnverifiedUser, WrongChannel
from discord import app_commands


def is_correct_channel():
    def predicate(interaction: discord.Interaction):
        if interaction.channel.id != LEADERBOARD_CHANNEL_ID:
            raise WrongChannel(f"Cannot use `{interaction.command.name}` in channel `{interaction.channel.name}`")
        return True
    return app_commands.check(predicate)


def is_correct_author():
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id not in VERIFIED_USERS:
            raise UnverifiedUser(f"User `{interaction.user.nick or interaction.user.name}` is not verified to run `{interaction.command.name}`")
        return True
    return app_commands.check(predicate)


async def setup(bot): pass
async def teardown(bot): pass
