from common.log import logger

import discord
from discord.ext import commands
from discord import app_commands

from services.db.val_database import (initialize_val_profile,
                                          remove_val_username_fromdb,
                                          update_val_username_indb)
from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel


class ValorantCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="add_valorant_profile",
                          description="Add a valorant profile to database. "
                                      "Accepts valorant username and tag "
                                      "(case-sensitive)")
    @is_correct_channel()
    async def addvalorantprofile(self, interaction: discord.Interaction,
                                  username: str, tag: str) -> None:
        """Adds valorant username and tag to database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Valorant username
        :param str tag: Valorant tag
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        try:
            puuid, region = await check_valorant_username(username, tag)

            response, existing_username = await initialize_val_profile(
                self.bot.db, username, puuid, tag, region, user_id, guild_id
            )

            if response:
                logger.info(f"{user_nick} ({user_id}) ran "
                            f"/add_valorant_profile with username "
                            f"'{username}#{tag}' successfully. "
                            f"Updated previously inactive profile "
                            f"'{existing_username}'")
                await interaction.followup.send(f"Successfully added "
                                                f"`{username}#{tag}` to the "
                                                f"database. Transferring "
                                                f"data from a previously "
                                                f"added profile "
                                                f"`{existing_username}`.")
            else:
                logger.info(f"{user_nick} ({user_id}) ran "
                            f"/add_valorant_profile with username "
                            f"'{username}#{tag}' successfully")
                await interaction.followup.send(f"Successfully added "
                                                f"`{username}#{tag}` to "
                                                f"the database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/add_valorant_profile with username "
                           f"'{username}#{tag}' -> {e.__class__.__name__}: "
                           f"{e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/add_valorant_profile with username '{username}#{tag}' -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="remove_valorant_profile",
                          description="Removes the valorant profile "
                                      "associated with your discord account "
                                      "from the database")
    @is_correct_channel()
    async def removevalorantprofile(self, interaction: discord.Interaction):
        """Remove valorant username and tag from database

        :param discord.Interaction interaction: Discord interaction
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.nick or interaction.user.name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        try:
            await remove_val_username_fromdb(self.bot.db, user_id, guild_id)
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/remove_valorant_profile successfully")
            await interaction.followup.send(f"Successfully removed "
                                            f"your username from the database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/remove_valorant_profile -> {e.__class__.__name__}: "
                           f"{e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /remove_valorant_profile with "
                f"username -> Unexpected error: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="update_valorant_profile",
                          description="Updates an existing valorant profile")
    @is_correct_channel()
    async def updatevalorantprofile(self, interaction: discord.Interaction,
                                   username: str, tag: str) -> None:
        """Updates an existing valorant profile in the database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Valorant username
        :param str tag: Valorant tag
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        try:
            puuid, region = await check_valorant_username(username, tag)
            await update_val_username_indb(
                self.bot.db, username, puuid, tag, region, user_id, guild_id
            )
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/update_valorant_profile successfully")
            await interaction.followup.send(f"Successfully updated "
                                            f"your profile in the database "
                                            f"to `{username}#{tag}`.")
        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/update_valorant_profile -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)

        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_valorant_profile -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    async def cog_app_command_error(self, interaction: discord.Interaction,
                                    e: app_commands.AppCommandError) -> None:
        if isinstance(e, CheckError):
            logger.warning(f"{interaction.user.nick or interaction.user.name} "
                           f"({interaction.user.id}) used "
                           f"{interaction.command.name} -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.response.send_message(e.message, ephemeral=True)
            return


async def setup(bot):
    await bot.add_cog(ValorantCommands(bot))
