import httpx
from nonebot import on_command, get_plugin_config
from nonebot.adapters.onebot.v11 import Message, Bot, Event, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
import random
import cairosvg
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="卡bin查询",
    description="用于查询信用卡的卡组织，卡等级，卡类型，发卡国家或地区等 (图片版)",
    homepage="https://github.com/bankcarddev/nonebot-plugin-binsearch",
    usage="/bin 533228",
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

config = get_plugin_config(Config)

# --- 资源路径定义 ---
PLUGIN_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(PLUGIN_DIR, "fonts")
ASSETS_DIR = os.path.join(PLUGIN_DIR, "assets")

# --- 字体配置 ---
DEFAULT_FONT_NAME = "STHUPO.TTF"  # 默认字体
BOLD_FONT_NAME = "STHUPO.TTF"    # 粗体字体 (如果与默认字体相同，则使用相同文件)
FALLBACK_FONT_NAMES = ["msyh.ttc", "arial.ttf", "DejaVuSans.ttf", "ヒラギノ角ゴシック W3.ttc", "Hiragino Sans GB W3.otf"]


def get_font_path(font_name, is_bold=False):
    """
    获取字体文件的有效路径。
    优先从插件的 `fonts` 目录加载，其次尝试系统字体。
    """
    preferred_font_filename = BOLD_FONT_NAME if is_bold else DEFAULT_FONT_NAME
    local_font_path = os.path.join(FONT_DIR, preferred_font_filename)
    if os.path.exists(local_font_path):
        return local_font_path

    if font_name:
        local_font_path_generic = os.path.join(FONT_DIR, font_name)
        if os.path.exists(local_font_path_generic):
            return local_font_path_generic

    for fb_font in FALLBACK_FONT_NAMES:
        try:
            ImageFont.truetype(fb_font, 10)
            return fb_font
        except IOError:
            continue
    return "sans-serif"

# 加载常规和粗体字体路径
FONT_REGULAR_PATH = get_font_path(DEFAULT_FONT_NAME, is_bold=False)
FONT_BOLD_PATH = get_font_path(BOLD_FONT_NAME, is_bold=True)

if FONT_BOLD_PATH == "sans-serif" and FONT_REGULAR_PATH != "sans-serif":
    FONT_BOLD_PATH = FONT_REGULAR_PATH
elif FONT_REGULAR_PATH == "sans-serif" and FONT_BOLD_PATH != "sans-serif":
    FONT_REGULAR_PATH = FONT_BOLD_PATH

# --- 卡组织 Logo 映射表 ---
SCHEME_LOGO_MAP = {
    "china union pay":    "unionpay",
    "american express":   "american_express",
    "mastercard":         "mastercard",
    "visa":               "visa",
    "discover":           "discover",
    "jcb":                "jcb",
}

async def query_bin_info(bin_number: str):
    """
    通过 RapidAPI 查询卡 BIN 信息。
    """
    url = "https://bin-ip-checker.p.rapidapi.com/"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": config.bin_api_key,
        "x-rapidapi-host": "bin-ip-checker.p.rapidapi.com",
    }
    query_params = {"bin": bin_number}
    json_payload = {"bin": bin_number}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=headers, params=query_params, json=json_payload
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        raise


def draw_rounded_rectangle_with_border(draw_context, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    if fill:
        draw_context.rounded_rectangle(xy, radius=radius, fill=fill)
    if outline and width > 0:
        draw_context.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
        draw_context.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
        draw_context.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
        draw_context.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)
        draw_context.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
        draw_context.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
        draw_context.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)
        draw_context.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)


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


def create_bin_image(bin_number_str: str, data: dict) -> BytesIO:
    # 随机图配置
    bg_name = "bg_" + str(random.randint(1, 2)) + ".png"
    bin_data = data.get('BIN', {})

    issuer_website = bin_data.get('issuer', {}).get('website') or "暂无"
    prepaid_text = "是" if bin_data.get('is_prepaid') == 'true' else "否"
    commercial_text = "是" if bin_data.get('is_commercial') == 'true' else "否"
    country_data = bin_data.get('country', {})
    issuer_data = bin_data.get('issuer', {})

    COLOR_ACCENT_PRIMARY = (0, 122, 255)
    COLOR_ACCENT_SECONDARY = (108, 117, 125)
    COLOR_TEXT_DARK = (33, 37, 41)
    COLOR_TEXT_MEDIUM = (73, 80, 87)
    COLOR_TEXT_LIGHT = (120, 120, 130)
    COLOR_FROST_LAYER = (255, 255, 255, 40)
    COLOR_CARD_BORDER = (255, 255, 255, 40)
    COLOR_SUCCESS = (255, 0, 0)             # “是”状态的绿色
    COLOR_INFO = (25, 135, 84)

    IMG_WIDTH = 800
    IMG_PADDING_HORIZONTAL = 50
    CARD_MARGIN_X = IMG_PADDING_HORIZONTAL
    CARD_MARGIN_Y_TOP = 30
    CARD_CORNER_RADIUS = 20
    CARD_BLUR_RADIUS = 4
    CARD_BORDER_WIDTH = 1

    try:
        font_main_title = ImageFont.truetype(FONT_BOLD_PATH, 36)
        font_bin_number = ImageFont.truetype(FONT_BOLD_PATH, 30)
        font_section_header = ImageFont.truetype(FONT_BOLD_PATH, 24)
        font_label = ImageFont.truetype(FONT_REGULAR_PATH, 20)
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
                ("银行名称", issuer_data.get('name', 'N/A')),
                ("官方网站", issuer_website),
            ],
        }
    ]

    card_padding_top = 30
    card_padding_horizontal = 30
    card_padding_bottom = 40
    title_area_height = 80
    section_header_height = 40
    line_item_height = 30
    space_between_sections = 20

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
        if background.size != (IMG_WIDTH, IMG_ACTUAL_HEIGHT):
            background = background.resize((IMG_WIDTH, IMG_ACTUAL_HEIGHT), Image.Resampling.LANCZOS)
    except FileNotFoundError:
        background = create_gradient_background(IMG_WIDTH, IMG_ACTUAL_HEIGHT, (40, 60, 80), (20, 30, 40))
        if background.mode != "RGBA":
            background = background.convert("RGBA")

    final_image = background.copy()
    draw = ImageDraw.Draw(final_image)

    card_x1, card_y1 = CARD_MARGIN_X, CARD_MARGIN_Y_TOP
    card_x2, card_y2 = card_x1 + CARD_WIDTH, card_y1 + CARD_ACTUAL_HEIGHT

    card_region_on_bg = final_image.crop((card_x1, card_y1, card_x2, card_y2))
    blurred_card_bg = card_region_on_bg.filter(ImageFilter.GaussianBlur(CARD_BLUR_RADIUS))
    final_image.paste(blurred_card_bg, (card_x1, card_y1))

    overlay_draw_img = Image.new("RGBA", final_image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay_draw_img)

    draw_rounded_rectangle_with_border(
        overlay_draw,
        (card_x1, card_y1, card_x2, card_y2),
        radius=CARD_CORNER_RADIUS,
        fill=COLOR_FROST_LAYER,
        outline=COLOR_CARD_BORDER if CARD_BORDER_WIDTH > 0 else None,
        width=CARD_BORDER_WIDTH,
    )
    final_image = Image.alpha_composite(final_image, overlay_draw_img)

    # 插入卡组织 Logo
    raw_scheme = bin_data.get('scheme', '')
    key = raw_scheme.strip().lower()
    logo_basename = SCHEME_LOGO_MAP.get(key)
    if logo_basename:
        logo_path = os.path.join(ASSETS_DIR, f"{logo_basename}.svg")
        if os.path.exists(logo_path):
            try:
                target_h = 40
                png_bytes = cairosvg.svg2png(url=logo_path, output_height=target_h)
                logo_img = Image.open(BytesIO(png_bytes)).convert("RGBA")
                final_image.paste(logo_img, (card_x1 + 30, card_y1 + 40), logo_img)
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
    value_start_x = text_start_x + 160

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
            try:
                value_width = draw.textlength(value, font=current_item_font)
            except AttributeError:
                value_width = draw.textsize(value, font=current_item_font)[0]

            if value_width > max_value_width:
                temp_value = value
                while len(temp_value) > 0:
                    try:
                        temp_width = draw.textlength(temp_value + "...", font=current_item_font)
                    except AttributeError:
                        temp_width = draw.textsize(temp_value + "...", font=current_item_font)[0]
                    if temp_width <= max_value_width:
                        value = temp_value + "..."
                        break
                    temp_value = temp_value[:-1]
                if not temp_value and value_width > max_value_width:
                    value = "..."

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

bin_query = on_command('bin', aliases={'BIN','Bin'}, priority=5, block=True)

@bin_query.handle()
async def handle_bin_query(bot: Bot, event: Event, arg: Message = CommandArg()):
    bin_number = arg.extract_plain_text().strip()

    if not bin_number:
        await bin_query.finish("�请输入卡BIN，例如：/bin 448590")
    if not bin_number.isdigit() or not (6 <= len(bin_number) <= 8):
        await bin_query.finish("🚫 卡BIN通常是6到8位数字，例如：/bin 448590")

    try:
        result = await query_bin_info(bin_number)
        if result.get('success', False) and result.get('BIN'):
            image_bytes = create_bin_image(bin_number, result)
            await bin_query.send(MessageSegment.image(image_bytes))
        else:
            await bin_query.finish("⚠️ 查询失败，请稍后再试。")
    except Exception:
        await bin_query.finish("❌ 查询失败，请稍后再试。")
