from dataclasses import dataclass
from typing import List, Callable
from settings import LEADERBOARD_TYPES
leaderboard_types_list = list(LEADERBOARD_TYPES.keys())


@dataclass
class LeaderboardRenderRow:
    user_id: int
    username: str
    score_display: str
    rank_id: int = None
    second_username: str = None


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
    draw_second_username: bool = False


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
    user_id, username, current_rank, rank_id, energy, second_username = row
    score_display = f"{energy} - {current_rank}"
    return LeaderboardRenderRow(
        user_id=user_id,
        username=username,
        score_display=score_display,
        rank_id=rank_id,
        second_username=second_username,
    )


def dojo_aimlabs_playlist_renderer(row):
    user_id, username, score, second_username = row
    return LeaderboardRenderRow(
        user_id=user_id,
        username=username,
        score_display=str(score),
        second_username=second_username,
    )


LEADERBOARD_RENDER_CONFIG = {
    leaderboard_types_list[0]: LeaderboardRendererConfig(
        title = "Valorant Rank Leaderboard",
        headers = ["#", "User", "Rank (RR)"],
        header_positions = [40, 270, 1560],
        score_position = 1680,
        rank_icon_position = 1430,
        draw_valorant_rank_icon = True,
        data_parser = valorant_rank_parser
    ),
    leaderboard_types_list[1]: LeaderboardRendererConfig(
        title = "Valorant DM and TDM Leaderboard",
        headers = ["#", "User", "DM Count"],
        header_positions = [40, 270, 1620],
        score_position = 1710,
        data_parser = valorant_dm_parser
    ),
    leaderboard_types_list[2]: LeaderboardRendererConfig(
        title = "Voltaic S5 (Kovaaks)",
        headers = ["#", "User", "Energy - Rank"],
        header_positions = [40, 270, 1540],
        score_position = 1680,
        rank_icon_position = 1430,
        draw_voltaic_rank_icon =  True,
        draw_second_username = True,
        data_parser = voltaic_s5_benchmark_leaderboard_parser
    ),
    leaderboard_types_list[3]: LeaderboardRendererConfig(
        title = "Voltaic VAL S1 (Aimlabs)",
        headers = ["#", "User", "Energy - Rank"],
        header_positions = [40, 270, 1540],
        score_position = 1680,
        rank_icon_position = 1430,
        draw_voltaic_val_rank_icon =  True,
        draw_second_username = True,
        data_parser = voltaic_s5_benchmark_leaderboard_parser
    ),
    leaderboard_types_list[4]: LeaderboardRendererConfig(
        title = "Balance Dojo Playlist (Aimlabs)",
        headers = ["#", "User", "Score"],
        header_positions = [40, 270, 1620],
        score_position = 1710,
        data_parser = dojo_aimlabs_playlist_renderer
    ),
    leaderboard_types_list[5]: LeaderboardRendererConfig(
        title = "Advanced Dojo Playlist (Aimlabs)",
        headers = ["#", "User", "Score"],
        header_positions = [40, 270, 1620],
        score_position = 1710,
        data_parser = dojo_aimlabs_playlist_renderer
    )
}


async def setup(bot): pass
async def teardown(bot): pass
