import settings
import discord
from discord.ext import commands
from utils.log import logger
from utils.checks import is_correct_channel, is_correct_author
from utils.errors import CheckError
import traceback

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.presences = True


bot = commands.Bot(command_prefix='/', intents=intents)


# List of extension/cog files to load
all_extensions = [
    # Config
    'settings',
    'configs.leaderboard_config',

    # Util functions
    'utils.log',
    'utils.errors',
    'utils.checks',
    'utils.api_helper',
    'utils.database_helper',
    'utils.image_gen',

    # Services API
    'services.api.val_api',
    'services.api.aimlabs_api',
    'services.api.kovaaks_api',

    # Services Database
    'services.db.database',
    'services.db.val_database',
    'services.db.aimlabs_database',
    'services.db.kovaaks_database',
    'services.db.leaderboard_database',

    # Cogs
    'cogs.aimlabs_commands',
    'cogs.valorant_commands',
    'cogs.kovaaks_commands',
    'cogs.help_commands',
    'cogs.database_commands',
    'cogs.leaderboard_commands',
    'cogs.assign_roles_commands'
    # 'cogs.rotating_leaderboard_commands'
]


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')

@bot.tree.command(name="reload", description="Reload bot commands. Ctrl+r on "
                                             "discord if they don't update. "
                                             "This may take a minute.")
@is_correct_author()
@is_correct_channel()
async def reload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    user_nick = interaction.user.nick or interaction.user.name
    user_id = interaction.user.id

    try:
        # Reload all extensions
        for extension in all_extensions:
            await bot.reload_extension(extension)

        synced_commands = await bot.tree.sync()
        logger.info(f"{user_nick} ({user_id}) ran /reload successfully -> "
                    f"reloaded {len(synced_commands)} commands and "
                    f"{len(all_extensions)} extensions")
        await interaction.followup.send(f"`{len(synced_commands)}` commands "
                                        f"and `{len(all_extensions)}` "
                                        f"extensions reloaded")
    except Exception as e:
        logger.error(
            f"{user_nick} ({user_id}) ran /reload -> Unexpected error: "
            f"{str(e)}\n{traceback.format_exc()}"
        )
        await interaction.followup.send(f"Ran into an unexpected error "
                                        f"(oopsie teehee).\n\n{str(e)}")


@reload.error
async def reload_error(interaction, e):
    if isinstance(e, CheckError):
        logger.warning(f"{interaction.user.display_name} "
                       f"({interaction.user.id}) used "
                       f"{interaction.command.name} -> "
                       f"{e.__class__.__name__}: {e.message}")
        await interaction.response.send_message(e.message, ephemeral=True)
        return


# Load initial extensions
async def setup_hook():
    for extension in all_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded extension {extension}")
            print(f"Loaded extension {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}"
                         f"{str(e)}\n{traceback.format_exc()}")
            print(f"Failed to load extension {extension}: {e}")
    try:
        synced_commands = await bot.tree.sync()
        print(f"Successfully loaded {len(synced_commands)} commands and "
              f"{len(all_extensions)} extensions")
    except Exception as e:
        logger.error(f"Failed to load {e}")


@bot.event
async def on_error(event, error, *args, **kwargs):
    # error = sys.exc_info()[1]
    error_message = f"Unhandled error in {event}: {error.__class__.__name__}: {error}"
    logger.error(error_message)


bot.setup_hook = setup_hook

bot.run(settings.DISCORD_API_SECRET, root_logger=True)
