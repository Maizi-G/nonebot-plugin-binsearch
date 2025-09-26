import os
from PIL import ImageFont, ImageDraw

PLUGIN_DIR = os.path.dirname(__file__)
FONT_DIR = os.path.join(PLUGIN_DIR, "fonts")

DEFAULT_FONT_NAME = "STHUPO.TTF"
BOLD_FONT_NAME = "STHUPO.TTF"
FALLBACK_FONT_NAMES = ["msyh.ttc", "arial.ttf", "DejaVuSans.ttf",
                       "ヒラギノ角ゴシック W3.ttc", "Hiragino Sans GB W3.otf"]

def get_font_path(font_name, is_bold=False):
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

def draw_rounded_rectangle_with_border(draw_context, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    if fill:
        draw_context.rounded_rectangle(xy, radius=radius, fill=fill)
    if outline and width > 0:
        draw_context.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
        draw_context.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
        draw_context.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
        draw_context.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)
