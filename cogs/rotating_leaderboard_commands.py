import discord
from discord.ext import commands
from discord import app_commands, ui, SelectOption
from utils.log import logger

from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel, is_correct_author


class CreateAimlabsLeaderboardModal(discord.ui.Modal, title="Create Aimlabs Leaderboard"):
    def __init__(self) -> None:
        super().__init__()
        self.add_item(discord.ui.TextInput(label="Short Input"))
        self.add_item(discord.ui.TextInput(label="Long Input", style=discord.TextStyle.long))


    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")
        embed.add_field(name="Short Input", value=self.children[0].value)
        embed.add_field(name="Long Input", value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])


class CreateKovaaksLeaderboardModal(discord.ui.Modal, title="Create Kovaaks Leaderboard"):
    def __init__(self) -> None:
        super().__init__()
        self.add_item(discord.ui.TextInput(label="Short Input"))
        self.add_item(discord.ui.TextInput(label="Long Input", style=discord.TextStyle.long))


    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")
        embed.add_field(name="Short Input", value=self.children[0].value)
        embed.add_field(name="Long Input", value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])


class SelectAimTrainer(discord.ui.Select):
    def __init__(self, view) -> None:
        self.view = view
        options = [
            SelectOption(label="Aimlabs", value="a"),
            SelectOption(label="Kovaaks", value="k"),
        ]
        super().__init__(placeholder="Choose aim trainer...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "a":
            await interaction.response.send_modal(CreateAimlabsLeaderboardModal())
        else:
            await interaction.response.send_modal(CreateKovaaksLeaderboardModal())


class CreateLeaderboardView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.add_item(SelectAimTrainer(self))


class RotatingLeaderboardsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @is_correct_author()
    @is_correct_channel()
    @app_commands.command(name="create_leaderboard",
                          description="Creates a new rotating leaderboard. "
                                      "Opens a modal to submit details")
    async def create_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        await interaction.followup.send(view=CreateLeaderboardView())
        logger.info(f"{user_nick} ({user_id}) ran /create_leaderboard")


async def setup(bot):
    await bot.add_cog(RotatingLeaderboardsCommands(bot))
async def teardown(bot): pass
