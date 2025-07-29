import pathlib
import os
from dotenv import load_dotenv

load_dotenv()

VALO_API_KEY = os.getenv("VALO_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
DOJO_GUILD_ID = int(os.getenv("DOJO_GUILD_ID"))
DSN = os.getenv("DSN")

BASE_DIR = pathlib.Path(__file__).parent

S5_VOLTAIC_BENCHMARKS_CONFIG = (BASE_DIR / "configs" /
                                "s5_voltaic_benchmarks_config.json")
S1_VOLTAIC_VAL_BENCHMARKS_CONFIG = ("/common/configs/"
                                    "s1_voltaic_val_benchmarks_config.json")

API_HEADER_FIELDS = {
    "val": {
        "rate_limit_field": "x-ratelimit-remaining",
        "reset_time_field": "x-ratelimit-reset",
        "reset_time": 60,
        "rate_limit": 30
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
        "reset_time": 60,
        "rate_limit": 100
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

