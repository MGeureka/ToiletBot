import os, asyncio, random
from PIL import Image, ImageDraw, ImageFont
from configs.leaderboard_config import LEADERBOARD_RENDER_CONFIG
from settings import (AVATAR_CACHE_DIR, AVATAR_CACHE_LOCK,
                      VALORANT_RANK_IMAGES_DIR, LEADERBOARD_TEMPLATE_DIR,
                      VOLTAIC_RANK_IMAGES_DIR, VOLTAIC_VAL_RANK_IMAGES_DIR,
                      FONTS_DIR)


# Constants
LEADERBOARD_PAGE_SIZE = 10  # Number of users per page
LEADERBOARD_WIDTH = 1920
LEADERBOARD_HEIGHT = 1280
AVATAR_SIZE = 100
BACKGROUND_COLOR = (32, 34, 37)  # Discord dark theme color
TEXT_COLOR = (255, 255, 255)  # White text
HEADER_COLOR = (114, 137, 218)  # Discord blurple for headers
ALT_ROW_COLOR = (47, 49, 54)  # Slightly lighter for alternating rows
HIGHLIGHT_COLOR = (255, 215, 0)  # Gold color for top 3


# Specify the path to your font files or use a default font
title_font = ImageFont.truetype(FONTS_DIR / "arial.ttf", 60)
header_font = ImageFont.truetype(FONTS_DIR / "arial.ttf", 45)
regular_font = ImageFont.truetype(FONTS_DIR / "arial.ttf", 45)
footer_font = ImageFont.truetype(FONTS_DIR / "arial.ttf", 24)


class LeaderboardRenderer:
    def __init__(self, leaderboard_type: str):
        self.title_height = 20
        self.title_width = None
        self.leaderboard_type = leaderboard_type
        self.config = LEADERBOARD_RENDER_CONFIG[leaderboard_type]
        self.template = Image.open(LEADERBOARD_TEMPLATE_DIR /
                                   f"{leaderboard_type}.png")
        self.template.load()
        self.header_y = 50
        self.row_start_y = self.header_y + 40
        self.row_height = ((LEADERBOARD_HEIGHT - self.row_start_y - 10)
                           // LEADERBOARD_PAGE_SIZE)
        self.mask = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE), 0)
        mask_draw = ImageDraw.Draw(self.mask)
        mask_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

    @staticmethod
    def create_placeholder_avatar(seed_value: int) -> Image.Image:
        """
        Create a placeholder avatar with a consistent color based on user ID
        """
        # Create a deterministic color based on the seed value
        random.seed(seed_value)
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)

        # Create a blank image
        avatar = Image.new('RGBA', (AVATAR_SIZE, AVATAR_SIZE), (r, g, b, 255))
        draw = ImageDraw.Draw(avatar)

        # Draw a circle
        draw.ellipse((2, 2, AVATAR_SIZE - 4, AVATAR_SIZE - 4), fill=(r + 20, g + 20, b + 20, 255),
                     outline=(255, 255, 255, 128))
        return avatar


    def draw_title(self, draw):
        title = self.config.title
        text_bbox = draw.textbbox((0, 0), title, font=title_font)
        self.title_width = text_bbox[2] - text_bbox[0]
        draw.text(
            ((LEADERBOARD_WIDTH - self.title_width) // 2,
             self.title_height),
            title,
            fill=HEADER_COLOR,
            font=title_font
        )


    def draw_headers(self, draw):
        for i, header in enumerate(self.config.headers):
            draw.text(
                (self.config.header_positions[i], self.header_y),
                header,
                fill=HEADER_COLOR,
                font=header_font
            )
        # Draw separator line
        draw.line([(30, self.header_y + 52),
                        (LEADERBOARD_WIDTH - 30,
                         self.header_y + 52)],
                       fill=HEADER_COLOR,
                       width=2)


    def draw_avatars(self, image, user_id, row_y):
        try:
            avatar_path = AVATAR_CACHE_DIR / f"{user_id}.jpeg"
            with AVATAR_CACHE_LOCK:
                avatar_img = Image.open(avatar_path)
                avatar_img.load()
            avatar_img = avatar_img.resize((AVATAR_SIZE, AVATAR_SIZE))
        except FileNotFoundError:
            avatar_img = self.create_placeholder_avatar(hash(user_id))


        # Apply mask to avatar
        masked_avatar = Image.new('RGBA', (AVATAR_SIZE, AVATAR_SIZE))
        masked_avatar.paste(avatar_img, (0, 0), self.mask)

        # Paste avatar onto leaderboard
        avatar_x = self.config.header_positions[1] - AVATAR_SIZE - 15
        image.paste(masked_avatar, (avatar_x, row_y), masked_avatar)


    def draw_rank_icon(self, image, rank_id, row_y, icon_type: str):
        if icon_type == "val":
            masked_rank_id = Image.open(VALORANT_RANK_IMAGES_DIR / f"{rank_id}.png")
            masked_rank_id = masked_rank_id.resize((AVATAR_SIZE, AVATAR_SIZE))
        elif icon_type == "voltaic":
            masked_rank_id = Image.open(VOLTAIC_RANK_IMAGES_DIR / f"{rank_id}.png")
            masked_rank_id = masked_rank_id.resize((AVATAR_SIZE - 30, AVATAR_SIZE))
        elif icon_type == "voltaic_val":
            masked_rank_id = Image.open(VOLTAIC_VAL_RANK_IMAGES_DIR /
                                        f"{rank_id}.png")
            masked_rank_id = masked_rank_id.resize((AVATAR_SIZE, AVATAR_SIZE))
        else:
            return

        avatar_x = self.config.rank_icon_position - AVATAR_SIZE - 15
        image.paste(masked_rank_id, (avatar_x, row_y), masked_rank_id)


    def draw_alternating_rows(self, draw, data):
        for i, _ in enumerate(data):
            row_y = self.row_start_y + (i * self.row_height) + 20
            if i % 2 == 1:
                draw.rectangle(
                    [(30, row_y - 10),
                     (LEADERBOARD_WIDTH - 30, row_y + self.row_height - 10)],
                    fill=ALT_ROW_COLOR
                )


    def draw_rows(self, image, draw, data, start_rank):
        for i, row_data in enumerate(data):
            parsed = self.config.data_parser(row_data)
            username = parsed.username
            score = parsed.score_display
            user_id = parsed.user_id
            rank_id = parsed.rank_id or None
            rank = start_rank + i + 1
            row_y = self.row_start_y + (i * self.row_height) + 20


            # Try to get user avatar or use placeholder
            self.draw_avatars(image, user_id, row_y)
            if self.config.draw_valorant_rank_icon and rank_id is not None:
                self.draw_rank_icon(image, rank_id, row_y, "val")
            if self.config.draw_voltaic_rank_icon and rank_id is not None:
                self.draw_rank_icon(image, rank_id, row_y, "voltaic")
            if self.config.draw_voltaic_val_rank_icon and rank_id is not None:
                self.draw_rank_icon(image, rank_id, row_y, "voltaic_val")

            # Draw rank with special highlighting for top 3
            rank_color = HIGHLIGHT_COLOR if rank <= 3 else TEXT_COLOR
            draw.text(
                (self.config.header_positions[0], row_y + 20),
                f"#{rank}",
                fill=rank_color,
                font=regular_font
            )

            # Draw username
            draw.text(
                (self.config.header_positions[1], row_y + 20),
                username,
                fill=TEXT_COLOR,
                font=regular_font
            )

            # Draw score
            bbox = draw.textbbox((0, 0), score, font=regular_font)
            text_width = bbox[2] - bbox[0]
            score_x = self.config.score_position - text_width // 2
            draw.text(
                (score_x, row_y + 20),
                str(score),
                fill=TEXT_COLOR,
                font=regular_font
            )


    @staticmethod
    def draw_footer(draw, current_page, total_pages):
        page_text = f"Page {current_page}/{total_pages}"
        text_bbox = draw.textbbox((0, 0), page_text, font=regular_font)
        page_width = text_bbox[2] - text_bbox[0]

        draw.text(
            ((LEADERBOARD_WIDTH - page_width) // 2, LEADERBOARD_HEIGHT - 50),
            page_text,
            fill=TEXT_COLOR,
            font=footer_font
        )


    def get_image(self, data, current_page, total_pages, start_rank):
        image = self.template.copy()
        draw = ImageDraw.Draw(image)
        self.draw_rows(image, draw, data, start_rank)
        self.draw_footer(draw, current_page, total_pages)
        # resize_scale = 0.75
        # size = (int(resize_scale * LEADERBOARD_WIDTH), int(resize_scale * LEADERBOARD_HEIGHT))
        # image = image.resize(size=size)
        # image = image.convert("RGB")
        return image


    def get_template(self, data):
        image = Image.new(size=(LEADERBOARD_WIDTH, LEADERBOARD_HEIGHT), color=BACKGROUND_COLOR, mode='RGB')
        draw = ImageDraw.Draw(image)
        self.draw_title(draw)
        self.draw_headers(draw)
        self.draw_alternating_rows(draw, data)
        image = image.convert('RGB')
        image.save(rf"C:\Users\partt\PycharmProjects\aimlabs_api_data\assets\leaderboard_templates\{self.leaderboard_type}.png")


async def delete_files_indir(directory: str):
    if not os.path.exists(directory):
        return

    file_list = await asyncio.to_thread(os.listdir, directory)

    for filename in file_list:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            await asyncio.to_thread(os.remove, file_path)


def _get_templates(leaderboard_type: str):
    ld_renderer = LeaderboardRenderer(leaderboard_type)
    ld_renderer.get_template(list(range(0, 10)))

async def setup(bot): pass
async def teardown(bot): pass


# if __name__ == '__main__':
#     _get_templates("voltaic_S1_valorant_benchmarks_leaderboard")
