import discord
from discord.ext import commands
from discord import app_commands
from utils.log import logger
from services.db.kovaaks_database import (initialize_kovaaks_profile,
                                          remove_kovaaks_username_fromdb,
                                          update_kovaaks_username_indb)
from services.db.discord_database import (check_discord_profile_exists,
                                          initialize_discord_profile,)
from services.api.kovaaks_api import check_kovaaks_username
from utils.errors import (WeakError, CheckError)
import traceback
from utils.checks import is_correct_channel


class KovaaksCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="add_kovaaks_profile",
                          description="Add a Kovaaks profile to the database. "
                                      "Accepts kovaaks username "
                                      "(case-sensitive)")
    @is_correct_channel()
    async def addkovaaksprofile(self,
                                 interaction: discord.Interaction,
                                 username: str) -> None:
        """Adds kovaaks username to database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Kovaaks username
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        if not await check_discord_profile_exists(self.bot.db, user_id,
                                                  guild_id):
            avatar_key = interaction.user.display_avatar.key
            await initialize_discord_profile(self.bot.db, user_id,
                                             user_nick, avatar_key, guild_id)
        try:
            kovaaks_id, steam_id, steam_username = \
                await check_kovaaks_username(username)

            response, existing_username = await initialize_kovaaks_profile(
                self.bot.db, username, str(kovaaks_id), steam_username,
                steam_id, user_id, guild_id
            )
            if response:
                logger.info(f"{user_nick} ({user_id}) ran "
                            f"/add_kovaaks_profile with "
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
                            f"/add_kovaaks_profile with username "
                            f"'{username}' successfully")
                await interaction.followup.send(f"Successfully added "
                                                f"`{username}` to the database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/add_kovaaks_profile with username '{username}' "
                           f"-> {e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran "
                f"/add_kovaaks_profile with username '{username}' -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="remove_kovaaks_profile",
                          description="Removes the kovaaks profile associated "
                                      "with your discord account from the "
                                      "database")
    @is_correct_channel()
    async def removekovaaksprofile(self,
                                    interaction: discord.Interaction) -> None:
        """Remove kovaaks profile from database

        :param discord.Interation interaction: Discord interaction
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        try:
            await remove_kovaaks_username_fromdb(self.bot.db, user_id, guild_id)
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/remove_kovaaks_profile successfully")
            await interaction.followup.send(f"Successfully removed "
                                            f"your username from the database")

        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/remove_kovaaks_profile -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /remove_kovaaks_profile -> "
                f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            )
            await interaction.followup.send(f"Ran into an unexpected error "
                                            f"(oopsie teehee).\n\n{str(e)}")


    @app_commands.command(name="update_kovaaks_profile",
                          description="Updates an existing kovaaks profile")
    @is_correct_channel()
    async def updatekovaaksprofile(self, interaction: discord.Interaction,
                                    username: str) -> None:
        """Updates an existing kovaaks profile in the database

        :param discord.Interaction interaction: Discord interaction
        :param str username: Kovaaks username
        :return: None
        """
        await interaction.response.defer(ephemeral=True)

        user_nick = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        try:
            kovaaks_id, steam_id, steam_username = \
                await check_kovaaks_username(username)
            await update_kovaaks_username_indb(self.bot.db, username,
                                               str(kovaaks_id),
                                               steam_username, steam_id,
                                               user_id, guild_id)
            logger.info(f"{user_nick} ({user_id}) ran "
                        f"/update_kovaaks_profile successfully")
            await interaction.followup.send(f"Successfully updated "
                                            f"your profile in the database "
                                            f"to `{username}`.")
        except WeakError as e:
            logger.warning(f"{user_nick} ({user_id}) ran "
                           f"/update_kovaaks_profile -> "
                           f"{e.__class__.__name__}: {e.message}")
            await interaction.followup.send(e.message)
        except Exception as e:
            logger.error(
                f"{user_nick} ({user_id}) ran /update_kovaaks_profile -> "
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
    await bot.add_cog(KovaaksCommands(bot))
