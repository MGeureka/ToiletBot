import discord
from discord.ext import commands
from discord import app_commands
from utils.log import logger
from services.db.aimlabs_database import (add_aimlabs_username_todb,
                                          remove_aimlabs_username_fromdb,
                                          update_aimlabs_username_indb)
from services.api.aimlabs_api import check_aimlabs_username
from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel


class AimLabsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="add_aimlabs_profile",
                          description="Add an aimlabs profile to the database. "
                                      "Accepts aimlabs username "
                                      "(case-sensitive)")
    @is_correct_channel()
    async def addaimlabsprofile(self,
                                 interaction: discord.Interaction,
                                 username: str) -> None:
        """Adds aimlabs username to database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Aimlabs username
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id

        try:
            aimlabs_id = await check_aimlabs_username(username)

            response, existing_username = await add_aimlabs_username_todb(
                username, aimlabs_id, user_nick, user_id)
            if response:
                logger.info(f"{user_nick} ({user_id}) ran "
                            f"/add_aimlabs_profile with "
                            f"username '{username}' successfully. "
                            f"Updated previously inactive profile "
                            f"'{existing_username}'")
                await interaction.followup.send(f"Successfully added "
                                                f"`{username}` to the "
                                                f"database. Transferring "
                                                f"data from a previously "
                                                f"added profile "
                                                f"`{existing_username}`.")
            else:
                logger.info(f"{user_nick} ({user_id}) ran "
                            f"/add_aimlabs_profile with username "
                            f"'{username}' successfully")
                await interaction.followup.send(f"Successfully added "
                                                f"`{username}` to database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/add_aimlabs_profile with username '{username}' "
                           f"-> {e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/add_aimlabs_profile with username '{username}' -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="remove_aimlabs_profile",
                          description="Removes the aimlabs username associated "
                                      "with your discord account from the "
                                      "database")
    @is_correct_channel()
    async def removeaimlabsprofile(self,
                                    interaction: discord.Interaction) -> None:
        """Remove aimlabs username from database

        :param discord.Interation interaction: Discord interaction
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        try:
            await remove_aimlabs_username_fromdb(user_id, user_nick)
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/remove_aimlabs_profile successfully")
            await interaction.followup.send(f"Successfully removed "
                                            f"your username from the database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/remove_aimlabs_username -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /remove_aimlabs_username -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="update_aimlabs_profile",
                          description="Updates an existing aimlabs profile")
    @is_correct_channel()
    async def updateaimlabsprofile(self, interaction: discord.Interaction,
                                    username: str) -> None:
        """Updates an existing aimlabs username in the database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Aimlabs username
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        try:
            aimlabs_id = await check_aimlabs_username(username)
            await update_aimlabs_username_indb(username, aimlabs_id,
                                               user_nick, user_id)
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/update_aimlabs_profile successfully")
            await interaction.followup.send(f"Successfully updated "
                                            f"your username in the database"
                                            f"to `{username}`.")
        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/update_aimlabs_profile -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)

        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_aimlabs_profile -> "
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
    await bot.add_cog(AimLabsCommands(bot))
