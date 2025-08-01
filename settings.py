import pathlib
import os
from dotenv import load_dotenv
import asyncio
import threading

load_dotenv()

DISCORD_API_SECRET = os.getenv("DISCORD_TOKEN")
VALO_API_KEY = os.getenv("VALO_API_KEY")
LEADERBOARD_CHANNEL_ID = int(os.getenv("LEADERBOARD_CHANNEL_ID"))

GUILD_ID = 1333243573440741458
BASE_DIR = pathlib.Path(__file__).parent

COGS_DIR = BASE_DIR / "cogs"
LEADERBOARD_CACHE_DIR = BASE_DIR / "cache" / "leaderboards"
DB_PATH = BASE_DIR / "data" / "database.db"
VALORANT_RANK_IMAGES_DIR = BASE_DIR / "assets" / "rank_images" / "valorant"
VOLTAIC_RANK_IMAGES_DIR = BASE_DIR / "assets" / "rank_images" / "voltaic"
VOLTAIC_VAL_RANK_IMAGES_DIR = (BASE_DIR / "assets" / "rank_images" /
                               "voltaic_valorant")
FONTS_DIR = BASE_DIR / "assets" / "fonts"
LOGS_DIR = BASE_DIR / "logs"
AVATAR_CACHE_DIR = BASE_DIR / "cache" / "avatars"
LEADERBOARD_TEMPLATE_DIR = BASE_DIR / "assets" / "leaderboard_templates"
S5_VOLTAIC_BENCHMARKS_CONFIG = (BASE_DIR / "configs" /
                                "s5_voltaic_benchmarks_config.json")
S1_VOLTAIC_VAL_BENCHMARKS_CONFIG = (BASE_DIR / "configs" /
                                         "s1_voltaic_val_benchmarks_config.json"
                                         )


LEADERBOARD_CACHE_LOCK = asyncio.Lock()
AVATAR_CACHE_LOCK = threading.Lock()

LEADERBOARD_TYPES = {
    "valorant_rank_leaderboard": ["Valorant Ranks", "Rank Leaderboard"],
    "valorant_dm_leaderboard": ["Valorant DMs & TDMs", "Total DM leaderboard"],
    "voltaic_S5_benchmarks_leaderboard": ["Voltaic S5", "Voltaic S5 benchmarks "
                                                        "leaderboard"],
    "voltaic_S1_valorant_benchmarks_leaderboard": ["Voltaic VAL S1",
                                                   "Voltaic VAL benchmarks "
                                                   "leaderboard"],
    "dojo_aimlabs_playlist_balanced": ["Balanced Dojo Aimlabs Playlist",
                                       "Balanced Dojo Aimlabs Playlist"],
    "dojo_aimlabs_playlist_advanced": ["Advanced Dojo Aimlabs Playlist",
                                       "Advanced Dojo Aimlabs Playlist"]
}

VERIFIED_USERS = [123229985791016961, 363658627950706698, 1266397087701139539]

API_HEADER_FIELDS = {
    "val": {
        "rate_limit_field": "x-ratelimit-remaining",
        "reset_time_field": "x-ratelimit-reset",
        "reset_time": 60,
        "rate_limit": 90
    },
    "aimlabs": {
        "rate_limit_field": "ip-ratelimit-remaining",
        "reset_time_field": "ip-ratelimit-reset",
        "reset_time": 60,
        "rate_limit": 10000
    },
    "kovaaks": {
        "rate_limit_field": "",
        "reset_time_field": "",
        "reset_time": "",
        "rate_limit": ""
    },
}

DOJO_AIMLABS_PLAYLIST_BALANCED = [
    "CsLevel.VT Lowgravity56.VT Refle.SXBIE3",
    "CsLevel.VT Lowgravity56.VT Peeks.SXBIMN",
    "CsLevel.VT Lowgravity56.VT Sinip.SXBIWU",
    "CsLevel.VT Lowgravity56.VT Dynam.SEML1U",
    "CsLevel.VT Lowgravity56.VT Lorys.SII0N0",
    "CsLevel.Lowgravity56.VT Straf.RX8M65",
    "CsLevel.VT Lowgravity56.VT Angle.SX9GAE"
]

DOJO_AIMLABS_PLAYLIST_ADVANCED = [
    "CsLevel.VT Lowgravity56.VT Refle.SXERI8",
    "CsLevel.Lowgravity56.VT Peeks.RLW020",
    "CsLevel.Lowgravity56.VT Sinip.RL5NX1",
    "CsLevel.VT Lowgravity56.VT Dynam.SEML1U",
    "CsLevel.VT Lowgravity56.VT Lorys.SII0N0",
    "CsLevel.Lowgravity56.VT Straf.RX8M65",
    "CsLevel.VT Lowgravity56.VT Angle.SX9GAE"
]

S5_VOLTAIC_RANKS = {
    0: {"name": "Unranked", "id": "0"},
    100: {"name": "Iron", "id": "1"},
    200: {"name": "Bronze", "id": "2"},
    300: {"name": "Silver", "id": "3"},
    400: {"name": "Gold", "id": "4"},
    500: {"name": "Platinum", "id": "5"},
    600: {"name": "Diamond", "id": "6"},
    700: {"name": "Jade", "id": "7"},
    800: {"name": "Master", "id": "8"},
    900: {"name": "Grandmaster", "id": "9"},
    1000: {"name": "Nova", "id": "10"},
    1100: {"name": "Astra", "id": "11"},
    1200: {"name": "Celestial", "id": "12"},
}

S5_VOLTAIC_RANKS_COMPLETE = {
    0: {"name": "Unranked", "id": "0"},
    100: {"name": "Iron*", "id": "13"},
    200: {"name": "Bronze*", "id": "14"},
    300: {"name": "Silver*", "id": "15"},
    400: {"name": "Gold*", "id": "16"},
    500: {"name": "Platinum*", "id": "17"},
    600: {"name": "Diamond*", "id": "18"},
    700: {"name": "Jade*", "id": "19"},
    800: {"name": "Master*", "id": "20"},
    900: {"name": "Grandmaster*", "id": "21"},
    1000: {"name": "Nova*", "id": "22"},
    1100: {"name": "Astra*", "id": "23"},
    1200: {"name": "Celestial*", "id": "24"},
}

S1_VAL_VOLTAIC_RANKS = {
    0: {"name": "Unranked", "id": "0"},
    100: {"name": "Iron", "id": "1"},
    200: {"name": "Bronze", "id": "2"},
    300: {"name": "Silver", "id": "3"},
    400: {"name": "Gold", "id": "4"},
    500: {"name": "Platinum", "id": "5"},
    600: {"name": "Diamond", "id": "6"},
    700: {"name": "Ascendant", "id": "7"},
    800: {"name": "Immortal", "id": "8"},
    900: {"name": "Radiant", "id": "9"},
    1000: {"name": "Elysian", "id": "10"},
    1100: {"name": "Aurora", "id": "11"},
    1200: {"name": "Angelic", "id": "12"},
}

S1_VAL_VOLTAIC_RANKS_COMPLETE = {
    0: {"name": "Unranked", "id": "0"},
    100: {"name": "Iron*", "id": "13"},
    200: {"name": "Bronze*", "id": "14"},
    300: {"name": "Silver*", "id": "15"},
    400: {"name": "Gold*", "id": "16"},
    500: {"name": "Platinum*", "id": "17"},
    600: {"name": "Diamond*", "id": "18"},
    700: {"name": "Ascendant*", "id": "19"},
    800: {"name": "Immortal*", "id": "20"},
    900: {"name": "Radiant*", "id": "21"},
    1000: {"name": "Elysian*", "id": "22"},
    1100: {"name": "Aurora*", "id": "23"},
    1200: {"name": "Angelic*", "id": "24"},
}


DOJO_RANK_ROLES = {
    0: 1399069042819469332,
    3: 1399068527197028382,
    4: 1399068524814799059,
    5: 1399068519609536603,
    6: 1399068066133839902,
    7: 1399068082521247810,
    8: 1399068315644596325,
    9: 1399068200724988101,
    10: 1399068152180248606,
    11: 1399068085373108325,
    12: 1399067599358267555,
    13: 1399067593599357180,
    14: 1399067552600162416,
    15: 1399066202139131954,
    16: 1399066171059208396,
    17: 1399066137207111700,
    18: 1399065715486490644,
    19: 1399065693688823919,
    20: 1399065571492102265,
    21: 1399065345783889982,
    22: 1399065284379279391,
    23: 1399065191655800932,
    24: 1399064941218238564,
    25: 1399064886633431040,
    26: 1399064736489803978,
    27: 1335441431157805096
}


async def setup(bot): pass
async def teardown(bot): pass
