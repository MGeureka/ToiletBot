import discord
from discord.ext import commands
from services.db.leaderboard_database import (
    get_valorant_rank_leaderboard_data,
    get_valorant_dm_leaderboard_data,
    get_voltaic_s5_benchmarks_leaderboard_data,
    get_voltaic_s1_val_benchmarks_leaderboard_data)


def assign_leader_roles(
        rank_leader, dm_leader, voltaic_leader, voltaic_val_leader
):
    pass


def remove_leader_roles(self):
    pass


def setup(bot): pass
def teardown(bot): pass
