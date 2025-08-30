import os
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from nonebot import on_command, get_plugin_config
from nonebot.adapters.onebot.v11 import Message, Bot, Event, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
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
DEFAULT_FONT_NAME = "STHUPO.TTF" # 默认字体
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

    if font_name: # 尝试通用的 font_name 参数指定的字体
        local_font_path_generic = os.path.join(FONT_DIR, font_name)
        if os.path.exists(local_font_path_generic):
            return local_font_path_generic

    for fb_font in FALLBACK_FONT_NAMES:
        try:
            ImageFont.truetype(fb_font, 10) # 尝试加载以验证字体是否可用
            return fb_font # Pillow 会在系统路径中查找此字体
        except IOError:
            continue
    return "sans-serif" # 最后的备选方案

# 加载常规和粗体字体路径
FONT_REGULAR_PATH = get_font_path(DEFAULT_FONT_NAME, is_bold=False)
FONT_BOLD_PATH = get_font_path(BOLD_FONT_NAME, is_bold=True)


if FONT_BOLD_PATH == "sans-serif" and FONT_REGULAR_PATH != "sans-serif":
    FONT_BOLD_PATH = FONT_REGULAR_PATH
elif FONT_REGULAR_PATH == "sans-serif" and FONT_BOLD_PATH != "sans-serif":
    FONT_REGULAR_PATH = FONT_BOLD_PATH


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
            response.raise_for_status() # 如果HTTP状态码是4xx或5xx，则抛出HTTPStatusError
            return response.json()
    except httpx.HTTPStatusError as e:
        error_body = ""
        try:
            error_body = e.response.json()
        except Exception:
            error_body = e.response.text
        raise Exception(f"API请求失败 ({e.response.status_code}) URL: {e.request.url} - 响应: {error_body}")
    except httpx.RequestError as e:
        raise Exception(f"API请求失败 (RequestError) URL: {e.request.url} - 错误: {str(e)}")
    except Exception as e:
        raise Exception(f"发生未知错误: {str(e)}")


def draw_rounded_rectangle_with_border(draw_context, xy, radius, fill=None, outline=None, width=1):
    """
    绘制带独立边框的圆角矩形。Pillow < 9.2.0 不直接支持 outline 和 width。
    此函数通过分别绘制填充和边框（线条和圆弧）来实现。
    """
    x1, y1, x2, y2 = xy
    if fill:
        draw_context.rounded_rectangle(xy, radius=radius, fill=fill)
    if outline and width > 0:
        # 绘制四条直线边框
        draw_context.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)  # Top
        draw_context.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)  # Bottom
        draw_context.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)  # Left
        draw_context.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)  # Right
        # 绘制四个圆角弧线
        draw_context.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
        draw_context.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
        draw_context.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)
        draw_context.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)


def create_gradient_background(width, height, color_start, color_end):
    """
    创建从上到下的线性渐变背景图像。
    """
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
    """
    根据 BIN 查询结果生成信息卡片图像。
    """
    bin_data = data['BIN']

    issuer_website = bin_data.get('issuer', {}).get('website') or "暂无"
    prepaid_text = "是" if bin_data.get('is_prepaid') == 'true' else "否"
    commercial_text = "是" if bin_data.get('is_commercial') == 'true' else "否"
    country_data = bin_data.get('country', {})
    issuer_data = bin_data.get('issuer', {})

    # --- 色彩定义 ---
    COLOR_ACCENT_PRIMARY = (0, 122, 255)      # 主强调色 (蓝)
    COLOR_ACCENT_SECONDARY = (108, 117, 125)  # 次强调色 (灰)
    COLOR_TEXT_DARK = (33, 37, 41)            # 深色文本
    COLOR_TEXT_MEDIUM = (73, 80, 87)          # 中灰文本
    COLOR_TEXT_LIGHT = (120, 120, 130)        # 浅灰文本
    COLOR_FROST_LAYER = (255, 255, 255, 180)  # 毛玻璃效果的半透明白色层 (RGBA)
    COLOR_CARD_BORDER = (255, 255, 255, 120)  # 卡片边框的半透明白色 (RGBA)
    COLOR_SUCCESS = (255, 0, 0)             # “是”状态的绿色
    COLOR_INFO = (25, 135, 84)             # “否”状态的青色

    # --- 图像与卡片尺寸 ---
    IMG_WIDTH = 800
    IMG_PADDING_HORIZONTAL = 50
    CARD_MARGIN_X = IMG_PADDING_HORIZONTAL
    CARD_MARGIN_Y_TOP = 30 # 从图像顶部到卡片顶部的距离
    CARD_CORNER_RADIUS = 20
    CARD_BLUR_RADIUS = 15
    CARD_BORDER_WIDTH = 1

    # --- 字体加载 ---
    try:
        font_main_title = ImageFont.truetype(FONT_BOLD_PATH, 36)
        font_bin_number = ImageFont.truetype(FONT_BOLD_PATH, 30)
        font_section_header = ImageFont.truetype(FONT_BOLD_PATH, 24)
        font_label = ImageFont.truetype(FONT_REGULAR_PATH, 20)
        font_value = ImageFont.truetype(FONT_REGULAR_PATH, 20)
    except Exception: # 如果自定义字体加载失败，使用 Pillow 默认字体
        font_main_title, font_bin_number, font_section_header, font_label, font_value = [
            ImageFont.load_default() for _ in range(5)
        ]

    # --- 内容分块定义 ---
    sections = [
        {
            "title": "卡片基本信息",
            "items": [
                ("卡号段 (BIN)", bin_data.get('number', 'N/A')),
                ("卡组织", bin_data.get('scheme', 'N/A')),
                ("卡片类型", f"{bin_data.get('type', 'N/A')} {bin_data.get('level', '')}".strip()),
                ("预付卡", prepaid_text, COLOR_SUCCESS if prepaid_text == "是" else COLOR_INFO),
                ("商用卡", commercial_text, COLOR_SUCCESS if commercial_text == "是" else COLOR_INFO),
            ]
        },
        {
            "title": "发行信息",
            "items": [
                ("国家或地区", f"{country_data.get('name', 'N/A')}"),
                ("代码", country_data.get('alpha2', 'N/A')),
                ("货币", bin_data.get('currency', 'N/A')),
            ]
        },
        {
            "title": "发卡机构",
            "items": [
                ("银行名称", issuer_data.get('name', 'N/A')),
                ("官方网站", issuer_website),
            ]
        }
    ]

    # --- 动态计算卡片高度 ---
    card_padding_top = 30
    card_padding_horizontal = 30
    card_padding_bottom = 40
    title_area_height = 80  # 主标题和BIN号区域的总高度
    section_header_height = 40 # 每个区块标题的高度
    line_item_height = 30   # 每行信息的高度
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


    bg_image_path = os.path.join(ASSETS_DIR, "bg.png")
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

    # 裁剪卡片区域并应用高斯模糊
    card_region_on_bg = final_image.crop((card_x1, card_y1, card_x2, card_y2))
    blurred_card_bg = card_region_on_bg.filter(ImageFilter.GaussianBlur(CARD_BLUR_RADIUS))
    final_image.paste(blurred_card_bg, (card_x1, card_y1))


    overlay_draw_img = Image.new("RGBA", final_image.size, (0,0,0,0))
    overlay_draw = ImageDraw.Draw(overlay_draw_img)


    draw_rounded_rectangle_with_border(
        overlay_draw,
        (card_x1, card_y1, card_x2, card_y2),
        radius=CARD_CORNER_RADIUS,
        fill=COLOR_FROST_LAYER,
        outline=COLOR_CARD_BORDER if CARD_BORDER_WIDTH > 0 else None,
        width=CARD_BORDER_WIDTH
    )
    final_image = Image.alpha_composite(final_image, overlay_draw_img)
    draw = ImageDraw.Draw(final_image)


    current_y = card_y1 + card_padding_top


    title_text = "银行卡 BIN 信息查询"
    try: w_title = draw.textlength(title_text, font=font_main_title)
    except AttributeError: w_title = draw.textsize(title_text, font=font_main_title)[0] 
    draw.text(
        (card_x1 + (CARD_WIDTH - w_title) / 2, current_y),
        title_text, font=font_main_title, fill=COLOR_ACCENT_PRIMARY
    )
    current_y += 45 # 主标题后间距

    # BIN 号
    bin_display_text = f"BIN: {bin_number_str}"
    try: w_bin = draw.textlength(bin_display_text, font=font_bin_number)
    except AttributeError: w_bin = draw.textsize(bin_display_text, font=font_bin_number)[0]
    draw.text(
        (card_x1 + (CARD_WIDTH - w_bin) / 2, current_y),
        bin_display_text, font=font_bin_number, fill=COLOR_TEXT_DARK
    )
    current_y += (title_area_height - 45) # 确保 title_area_height 被用完

    # 各信息区块
    text_start_x = card_x1 + card_padding_horizontal
    value_start_x = text_start_x + 160 # 标签和值之间的固定间距

    for section in sections:
        draw.text(
            (text_start_x, current_y),
            section["title"],
            font=font_section_header,
            fill=COLOR_ACCENT_SECONDARY
        )
        current_y += section_header_height

        for item in section["items"]:
            label, value = item[0], str(item[1])
            color = item[2] if len(item) > 2 else COLOR_TEXT_MEDIUM

            draw.text(
                (text_start_x, current_y),
                f"{label}:", font=font_label, fill=COLOR_TEXT_LIGHT
            )

            # 处理可能过长文本的截断 (特别是网站和银行名称)
            current_item_font = font_value
            max_value_width = (card_x1 + CARD_WIDTH - card_padding_horizontal) - value_start_x - 5 # 减去一些边距
            try: value_width = draw.textlength(value, font=current_item_font)
            except AttributeError: value_width = draw.textsize(value, font=current_item_font)[0]

            if value_width > max_value_width:
                temp_value = value
                while len(temp_value) > 0:
                    try: temp_width = draw.textlength(temp_value + "...", font=current_item_font)
                    except AttributeError: temp_width = draw.textsize(temp_value + "...", font=current_item_font)[0]
                    if temp_width <= max_value_width:
                        value = temp_value + "..."
                        break
                    temp_value = temp_value[:-1]
                if not temp_value and value_width > max_value_width: # 如果截断后为空，显示省略号
                    value = "..."

            draw.text(
                (value_start_x, current_y),
                value, font=current_item_font, fill=color
            )
            current_y += line_item_height

        current_y += space_between_sections # 区块间距


    img_byte_arr = BytesIO()
    final_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


bin_query = on_command('bin', aliases={'BIN','Bin'}, priority=5, block=True)

@bin_query.handle()
async def handle_bin_query(bot: Bot, event: Event, arg: Message = CommandArg()):
    bin_number = arg.extract_plain_text().strip()

    if not bin_number:
        await bin_query.finish("🤔 请输入卡BIN，例如：/bin 448590")
    if not bin_number.isdigit() or not (6 <= len(bin_number) <= 8): # 常见BIN长度为6位，部分可能到8位
        await bin_query.finish("🚫 卡BIN通常是6到8位数字，例如：/bin 448590")

    try:

        result = await query_bin_info(bin_number)

        if result.get('success', False) and result.get('BIN'):
            image_bytes = create_bin_image(bin_number, result)
            await bin_query.send(MessageSegment.image(image_bytes))
        elif 'message' in result and not result.get('success', False):
            await bin_query.finish(f"⚠️ API查询失败：{result['message']}")
        else:
            error_detail = result.get('message', '请检查BIN号是否正确或API响应异常。')
            if not result.get('success', False) and not result.get('BIN') and 'message' not in result:
                 error_detail = f"API返回了非预期的空数据或无效数据。BIN: {bin_number}"
            await bin_query.finish(f"⚠️ 查询失败，{error_detail}")

    except Exception as e:
        error_message = str(e)
        # 格式化常见的 API 错误信息
        if "API请求失败 (400)" in error_message: error_message = "API请求失败：无效的卡BIN或请求格式错误 (400 Bad Request)。"
        elif "API请求失败 (401)" in error_message or "API请求失败 (403)" in error_message : error_message = "API请求失败：API密钥无效或未授权 (401/403)。请检查插件配置。"
        elif "API请求失败 (429)" in error_message: error_message = "API请求失败：请求频率过高，请稍后再试 (429 Too Many Requests)。"
        elif "API请求失败 (5" in error_message: error_message = "API请求失败：上游服务器错误，请稍后再试。" # 捕获所有5xx错误
        elif "API请求失败 (RequestError)" in error_message: error_message = "API请求失败：网络连接错误或无法访问API服务。"
        # 其他未知错误

        # 在用户端发送简化的错误信息
        await bin_query.send(f"❌ 查询时发生严重错误，请联系管理员或查看后台日志。\n错误摘要: {error_message.splitlines()[0]}")

        # 在后台打印完整的错误堆栈信息以供调试
        import traceback
        print(f"--- 卡BIN查询插件发生错误 (BIN: {bin_number}) ---")
        traceback.print_exc()
        print("--- 错误结束 ---")