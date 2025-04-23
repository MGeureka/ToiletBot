from dataclasses import dataclass
from typing import List, Callable
from settings import LEADERBOARD_TYPES
leaderboard_types_list = list(LEADERBOARD_TYPES.keys())


@dataclass
class LeaderboardRenderRow:
    user_id: int
    username: str
    score_display: str
    rank_id: int = None  # optional


@dataclass
class LeaderboardRendererConfig:
    title: str
    headers: List[str]
    header_positions: List[int]
    score_position: int
    data_parser: Callable[[tuple], LeaderboardRenderRow]
    rank_icon_position: int = None
    draw_valorant_rank_icon: bool = False
    draw_voltaic_rank_icon: bool = False
    draw_voltaic_val_rank_icon: bool = False


def valorant_rank_parser(row):
    user_id, username, current_rank, rank_id, rr = row
    score_display = f"{current_rank} ({rr})"
    return LeaderboardRenderRow(
        user_id=user_id,
        username=username,
        score_display=score_display,
        rank_id=rank_id,
    )


def valorant_dm_parser(row):
    user_id, username, score = row
    return LeaderboardRenderRow(
        user_id=user_id,
        username=username,
        score_display=str(score)
    )


def voltaic_s5_benchmark_leaderboard_parser(row):
    user_id, username, current_rank, rank_id, energy = row
    score_display = f"{energy} - {current_rank}"
    return LeaderboardRenderRow(
        user_id=user_id,
        username=username,
        score_display=score_display,
        rank_id=rank_id,
    )


LEADERBOARD_RENDER_CONFIG = {
    leaderboard_types_list[0]: LeaderboardRendererConfig(
        title = "Valorant Rank Leaderboard",
        headers = ["#", "User", "Rank (RR)"],
        header_positions = [50, 250, 1560],
        score_position = 1680,
        rank_icon_position = 1500,
        draw_valorant_rank_icon = True,
        data_parser = valorant_rank_parser
    ),
    leaderboard_types_list[1]: LeaderboardRendererConfig(
        title = "Valorant DM and TDM Leaderboard",
        headers = ["#", "User", "DM Count"],
        header_positions = [50, 250, 1620],
        score_position = 1710,
        data_parser = valorant_dm_parser
    ),
    leaderboard_types_list[2]: LeaderboardRendererConfig(
        title = "Voltaic S5",
        headers = ["#", "User", "Energy - Rank"],
        header_positions = [50, 250, 1540],
        score_position = 1680,
        rank_icon_position = 1520,
        draw_voltaic_rank_icon =  True,
        data_parser = voltaic_s5_benchmark_leaderboard_parser
    ),
    leaderboard_types_list[3]: LeaderboardRendererConfig(
        title = "Voltaic VAL S1",
        headers = ["#", "User", "Energy - Rank"],
        header_positions = [50, 250, 1540],
        score_position = 1680,
        rank_icon_position = 1520,
        draw_voltaic_val_rank_icon =  True,
        data_parser = voltaic_s5_benchmark_leaderboard_parser
    )
}


async def setup(bot): pass
async def teardown(bot): pass
