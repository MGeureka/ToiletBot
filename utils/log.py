from configs import log_config


logger = log_config.logging.getLogger("bot")
api_logger = log_config.logging.getLogger("api")
db_logger = log_config.logging.getLogger("db")


async def setup(bot): pass
async def teardown(bot): pass
