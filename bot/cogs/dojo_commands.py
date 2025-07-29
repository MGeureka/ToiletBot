import discord
from discord.ext import commands
from discord import app_commands

@app_commands.guilds(1352688724093304842)
class DojoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ppsize")
    async def ppsize(self, interaction: discord.Interaction):
        message = (f"Measuring {interaction.user.mention}..."
                   f"\n"
                   f"\n"
                   f"`Error`: Unable to measure"
                   f"\n"
                   f"`Reason`: Too small")
        await interaction.response.send_message(message)


async def setup(bot):
    await bot.add_cog(DojoCommands(bot))
async def teardown(bot): pass
