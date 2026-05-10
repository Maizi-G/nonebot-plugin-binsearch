import cairosvg
import os
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .utils import get_font_path, draw_rounded_rectangle_with_border

PLUGIN_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(PLUGIN_DIR, "assets")

# 字体
FONT_REGULAR_PATH = get_font_path("STHUPO.TTF")
FONT_BOLD_PATH = get_font_path("STHUPO.TTF")

# 卡组织 logo 映射
SCHEME_LOGO_MAP = {
    "china union pay": "unionpay",
    "american express": "american_express",
    "mastercard": "mastercard",
    "visa": "visa",
    "discover": "discover",
    "jcb": "jcb",
}


def truncate_text_smart(text, max_width, font, draw):
    """Smart text truncation that preserves important parts like domains"""
    try:
        text_width = draw.textlength(text, font=font)
    except AttributeError:
        text_width = draw.textsize(text, font=font)[0]

    if text_width <= max_width:
        return text

    # For URLs, try to preserve domain
    if text.startswith('http'):
        parts = text.split('/')
        if len(parts) >= 3:
            domain = '/'.join(parts[:3])
            try:
                domain_width = draw.textlength(domain + "...", font=font)
            except AttributeError:
                domain_width = draw.textsize(domain + "...", font=font)[0]
            if domain_width <= max_width:
                return domain + "..."

    # Standard truncation
    temp_text = text
    while len(temp_text) > 3:
        try:
            truncated_width = draw.textlength(temp_text[:-3] + "...", font=font)
        except AttributeError:
            truncated_width = draw.textsize(temp_text[:-3] + "...", font=font)[0]
        if truncated_width <= max_width:
            return temp_text[:-3] + "..."
        temp_text = temp_text[:-1]
    return "..."


def draw_section_separator(draw, x1, x2, y):
    """Draw a subtle gradient line separator between sections"""
    for i in range(3):
        alpha = 80 - (i * 20)
        draw.line([(x1 + 10, y + i), (x2 - 10, y + i)],
                  fill=(200, 200, 210, alpha), width=1)


def draw_status_badge(draw, x, y, color):
    """Draw a small colored badge indicator"""
    badge_radius = 4
    badge_x = x - 12
    badge_y = y + 8
    draw.ellipse(
        [(badge_x - badge_radius, badge_y - badge_radius),
         (badge_x + badge_radius, badge_y + badge_radius)],
        fill=color
    )


def create_bin_image(bin_number_str: str, data: dict) -> BytesIO:
    # 随机图配置
    bg_name = "bg_" + str(random.randint(1, 4)) + ".png"
    bin_data = data.get('BIN', {})

    issuer_website = bin_data.get('issuer', {}).get('website') or "暂无"
    prepaid_text = "是" if bin_data.get('is_prepaid') == 'true' else "否"
    commercial_text = "是" if bin_data.get('is_commercial') == 'true' else "否"
    country_data = bin_data.get('country', {})
    issuer_data = bin_data.get('issuer', {})

    COLOR_ACCENT_PRIMARY = (0, 122, 255)
    COLOR_ACCENT_SECONDARY = (88, 97, 115)
    COLOR_TEXT_DARK = (20, 24, 28)
    COLOR_TEXT_MEDIUM = (60, 67, 74)
    COLOR_TEXT_LIGHT = (108, 115, 125)
    COLOR_FROST_LAYER = (255, 255, 255, 50)
    COLOR_CARD_BORDER = (255, 255, 255, 60)
    COLOR_SUCCESS = (25, 135, 84)
    COLOR_INFO = (13, 110, 253)

    IMG_WIDTH = 1000
    IMG_PADDING_HORIZONTAL = 80
    CARD_MARGIN_X = IMG_PADDING_HORIZONTAL
    CARD_MARGIN_Y_TOP = 40
    CARD_CORNER_RADIUS = 24
    CARD_BLUR_RADIUS = 3
    CARD_BORDER_WIDTH = 2

    try:
        font_main_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_bin_number = ImageFont.truetype(FONT_BOLD_PATH, 32)
        font_section_header = ImageFont.truetype(FONT_BOLD_PATH, 26)
        font_label = ImageFont.truetype(FONT_REGULAR_PATH, 19)
        font_value = ImageFont.truetype(FONT_REGULAR_PATH, 20)
    except Exception:
        font_main_title, font_bin_number, font_section_header, font_label, font_value = [
            ImageFont.load_default() for _ in range(5)
        ]

    sections = [
        {
            "title": "卡片基本信息",
            "items": [
                ("卡号段 (BIN)", bin_data.get('number', 'N/A')),
                ("卡组织", bin_data.get('scheme', 'N/A')),
                ("卡片类型", f"{bin_data.get('type', 'N/A')} {bin_data.get('level', '')}".strip()),
                ("预付卡", prepaid_text, COLOR_SUCCESS if prepaid_text == "是" else COLOR_INFO),
                ("商用卡", commercial_text, COLOR_SUCCESS if commercial_text == "是" else COLOR_INFO),
            ],
        },
        {
            "title": "发行信息",
            "items": [
                ("国家或地区", f"{country_data.get('name', 'N/A')}"),
                ("代码", country_data.get('alpha2', 'N/A')),
                ("货币", bin_data.get('currency', 'N/A')),
            ],
        },
        {
            "title": "发卡机构",
            "items": [
                ("银行或机构名称", issuer_data.get('name', 'N/A')),
                ("官方网站", issuer_website),
            ],
        }
    ]

    card_padding_top = 40
    card_padding_horizontal = 40
    card_padding_bottom = 50
    title_area_height = 100
    section_header_height = 50
    line_item_height = 36
    space_between_sections = 30

    calculated_card_content_height = title_area_height
    for idx, section in enumerate(sections):
        calculated_card_content_height += section_header_height
        calculated_card_content_height += len(section["items"]) * line_item_height
        if idx < len(sections) - 1:
            calculated_card_content_height += space_between_sections

    CARD_ACTUAL_HEIGHT = card_padding_top + calculated_card_content_height + card_padding_bottom
    IMG_ACTUAL_HEIGHT = CARD_ACTUAL_HEIGHT + 2 * CARD_MARGIN_Y_TOP
    CARD_WIDTH = IMG_WIDTH - 2 * CARD_MARGIN_X

    bg_image_path = os.path.join(ASSETS_DIR, bg_name)
    try:
        background = Image.open(bg_image_path)
        if background.mode != "RGBA":
            background = background.convert("RGBA")

        # 保持原始比例，裁剪或填充到目标尺寸
        bg_width, bg_height = background.size
        target_ratio = IMG_WIDTH / IMG_ACTUAL_HEIGHT
        bg_ratio = bg_width / bg_height

        if bg_ratio > target_ratio:
            # 背景更宽，按高度缩放后裁剪宽度
            new_height = IMG_ACTUAL_HEIGHT
            new_width = int(bg_width * (IMG_ACTUAL_HEIGHT / bg_height))
            background = background.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # 居中裁剪
            left = (new_width - IMG_WIDTH) // 2
            background = background.crop((left, 0, left + IMG_WIDTH, IMG_ACTUAL_HEIGHT))
        else:
            # 背景更高，按宽度缩放后裁剪高度
            new_width = IMG_WIDTH
            new_height = int(bg_height * (IMG_WIDTH / bg_width))
            background = background.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # 居中裁剪
            top = (new_height - IMG_ACTUAL_HEIGHT) // 2
            background = background.crop((0, top, IMG_WIDTH, top + IMG_ACTUAL_HEIGHT))
    except FileNotFoundError:
        background = create_gradient_background(IMG_WIDTH, IMG_ACTUAL_HEIGHT, (40, 60, 80), (20, 30, 40))
        if background.mode != "RGBA":
            background = background.convert("RGBA")

    final_image = background.copy()
    draw = ImageDraw.Draw(final_image)

    card_x1, card_y1 = CARD_MARGIN_X, CARD_MARGIN_Y_TOP
    card_x2, card_y2 = card_x1 + CARD_WIDTH, card_y1 + CARD_ACTUAL_HEIGHT

    # 液态玻璃效果：多层模糊 + 渐变透明度
    card_region_on_bg = final_image.crop((card_x1, card_y1, card_x2, card_y2))

    # 第一层：强模糊
    blurred_layer1 = card_region_on_bg.filter(ImageFilter.GaussianBlur(CARD_BLUR_RADIUS * 2))
    # 第二层：中等模糊
    blurred_layer2 = card_region_on_bg.filter(ImageFilter.GaussianBlur(CARD_BLUR_RADIUS))

    # 混合两层模糊创造液态感
    blurred_card_bg = Image.blend(blurred_layer1, blurred_layer2, 0.5)
    final_image.paste(blurred_card_bg, (card_x1, card_y1))

    overlay_draw_img = Image.new("RGBA", final_image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay_draw_img)

    # 液态玻璃：渐变透明度的多层效果
    # 第一层：底层半透明白色
    draw_rounded_rectangle_with_border(
        overlay_draw,
        (card_x1, card_y1, card_x2, card_y2),
        radius=CARD_CORNER_RADIUS,
        fill=(255, 255, 255, 35),
        outline=None,
        width=0,
    )

    # 第二层：顶部高光渐变
    gradient_overlay = Image.new("RGBA", final_image.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient_overlay)

    # 创建从上到下的渐变高光
    card_height = card_y2 - card_y1
    for i in range(int(card_height * 0.4)):  # 只在顶部40%添加高光
        alpha = int(30 * (1 - i / (card_height * 0.4)))  # 从30渐变到0
        gradient_draw.line(
            [(card_x1, card_y1 + i), (card_x2, card_y1 + i)],
            fill=(255, 255, 255, alpha),
            width=1
        )

    overlay_draw_img = Image.alpha_composite(overlay_draw_img, gradient_overlay)

    # 第三层：边框光晕
    border_overlay = Image.new("RGBA", final_image.size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_overlay)
    draw_rounded_rectangle_with_border(
        border_draw,
        (card_x1, card_y1, card_x2, card_y2),
        radius=CARD_CORNER_RADIUS,
        fill=None,
        outline=(255, 255, 255, 80),
        width=CARD_BORDER_WIDTH,
    )

    overlay_draw_img = Image.alpha_composite(overlay_draw_img, border_overlay)
    final_image = Image.alpha_composite(final_image, overlay_draw_img)

    # 插入卡组织 Logo
    raw_scheme = bin_data.get('scheme', '')
    key = raw_scheme.strip().lower()
    logo_basename = SCHEME_LOGO_MAP.get(key)
    if logo_basename:
        logo_path = os.path.join(ASSETS_DIR, f"{logo_basename}.svg")
        if os.path.exists(logo_path):
            try:
                target_h = 45
                png_bytes = cairosvg.svg2png(url=logo_path, output_height=target_h)
                logo_img = Image.open(BytesIO(png_bytes)).convert("RGBA")
                logo_x = card_x2 - 25 - logo_img.width
                logo_y = card_y1 + 25
                final_image.paste(logo_img, (logo_x, logo_y), logo_img)
            except Exception:
                pass

    draw = ImageDraw.Draw(final_image)

    current_y = card_y1 + card_padding_top
    title_text = "银行卡 BIN 信息查询"
    try:
        w_title = draw.textlength(title_text, font=font_main_title)
    except AttributeError:
        w_title = draw.textsize(title_text, font=font_main_title)[0]

    draw.text(
        (card_x1 + (CARD_WIDTH - w_title) / 2, current_y),
        title_text, font=font_main_title, fill=COLOR_ACCENT_PRIMARY
    )
    current_y += 45

    bin_display_text = f"BIN: {bin_number_str}"
    try:
        w_bin = draw.textlength(bin_display_text, font=font_bin_number)
    except AttributeError:
        w_bin = draw.textsize(bin_display_text, font=font_bin_number)[0]
    draw.text(
        (card_x1 + (CARD_WIDTH - w_bin) / 2, current_y),
        bin_display_text, font=font_bin_number, fill=COLOR_TEXT_DARK
    )
    current_y += (title_area_height - 45)

    text_start_x = card_x1 + card_padding_horizontal

    # Calculate dynamic label column width based on longest label
    max_label_width = 0
    for section in sections:
        for item in section["items"]:
            label_text = item[0] + ":"
            try:
                label_width = draw.textlength(label_text, font=font_label)
            except AttributeError:
                label_width = draw.textsize(label_text, font=font_label)[0]
            max_label_width = max(max_label_width, label_width)

    value_start_x = text_start_x + max_label_width + 20

    for section in sections:
        draw.text(
            (text_start_x, current_y),
            section["title"],
            font=font_section_header,
            fill=COLOR_ACCENT_SECONDARY,
        )
        current_y += section_header_height

        for item in section["items"]:
            label, value = item[0], str(item[1])
            color = item[2] if len(item) > 2 else COLOR_TEXT_MEDIUM

            draw.text(
                (text_start_x, current_y),
                f"{label}:", font=font_label, fill=COLOR_TEXT_LIGHT
            )

            current_item_font = font_value
            max_value_width = (card_x1 + CARD_WIDTH - card_padding_horizontal) - value_start_x - 5

            # Use smart truncation
            value = truncate_text_smart(value, max_value_width, current_item_font, draw)

            # Draw status badge for yes/no fields
            if label in ["预付卡", "商用卡"]:
                badge_color = COLOR_SUCCESS if value == "是" else COLOR_TEXT_LIGHT
                draw_status_badge(draw, value_start_x, current_y, badge_color)

            draw.text(
                (value_start_x, current_y),
                value, font=current_item_font, fill=color
            )
            current_y += line_item_height

        current_y += space_between_sections

    img_byte_arr = BytesIO()

    final_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


def create_gradient_background(width, height, color_start, color_end):
    base = Image.new("RGB", (width, height), color_start)
    draw = ImageDraw.Draw(base)
    for y in range(height):
        factor = y / height
        r = int(color_start[0] * (1 - factor) + color_end[0] * factor)
        g = int(color_start[1] * (1 - factor) + color_end[1] * factor)
        b = int(color_start[2] * (1 - factor) + color_end[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return base