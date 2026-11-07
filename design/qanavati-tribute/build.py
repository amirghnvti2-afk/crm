#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qanavati family tribute — two 1080x1920 Instagram / WhatsApp story images.

Art direction: quiet luxury + minimal editorial layout + refined Persian
typography (Vazirmatn). Text is shaped with HarfBuzz and rasterised with
FreeType at 2x supersampling, so the Persian copy is reproduced exactly as
authored (no AI-image text artefacts).

Usage:  python3 build.py            # both stories  -> out/
        python3 build.py --test     # layout test sheet -> out/_test.png
"""

import os
import sys
import numpy as np
import freetype
import uharfbuzz as hb
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "out")

W, H = 1080, 1920
SS = 2  # supersampling

# ---------------------------------------------------------------- palette ----
PAPER = (248, 244, 235)      # warm ivory, fine-art paper
INK = (35, 34, 30)           # soft charcoal
INK_DEEP = (28, 27, 24)
ACCENT = (116, 128, 122)     # muted blue-green
HAIR_ACCENT = (150, 160, 154)
HAIR_FAINT = (196, 189, 175)

# ------------------------------------------------- exact copy (do not edit) --
BASMALA = "بسمه‌تعالی"

STORY1 = (
    "با نهایت احترام و امتنان، بر خود لازم می‌دانم از تمامی استادان ارجمند، "
    "همکاران گرامی، مسئولان محترم، بستگان، دوستان و آشنایان عزیزی که با حضور "
    "ارزشمند خود در مراسم تشییع و بزرگداشت شادروان حاج منصور قنواتی و همچنین "
    "با تماس‌ها، پیام‌ها و ابراز همدردی، موجب تسلی خاطر اینجانب و خانواده شدند، "
    "صمیمانه قدردانی و سپاسگزاری نمایم."
)

STORY2_P1 = (
    "بی‌تردید محبت، بزرگواری و همراهی شما عزیزان در این روزهای دشوار، "
    "برای ما بسیار ارزشمند و فراموش‌نشدنی است."
)

STORY2_P2 = (
    "از درگاه خداوند متعال برای یکایک شما و خانواده‌های محترمتان سلامتی و عزت، "
    "و برای آن مرحوم رحمت واسعه و علو درجات مسئلت دارم."
)

# Hand-set breaks for the short paragraphs (checked against the column width),
# so no line ends on a bare conjunction and no widow is left dangling.
STORY2_P1_LINES = [
    "بی‌تردید محبت، بزرگواری و همراهی شما",
    "عزیزان در این روزهای دشوار، برای ما",
    "بسیار ارزشمند و فراموش‌نشدنی است.",
]
STORY2_P2_LINES = [
    "از درگاه خداوند متعال برای یکایک شما",
    "و خانواده‌های محترمتان سلامتی و عزت،",
    "و برای آن مرحوم رحمت واسعه",
    "و علو درجات مسئلت دارم.",
]

SIGN_LEAD = "با سپاس و احترام"
SIGN_NAME = "خانواده قنواتی"


# ------------------------------------------------------------------- type ----
class TypeFace:
    def __init__(self, filename):
        path = os.path.join(FONTS, filename)
        blob = hb.Blob.from_file_path(path)
        self.hb_face = hb.Face(blob)
        self.hb_font = hb.Font(self.hb_face)
        self.upem = self.hb_face.upem
        self.hb_font.scale = (self.upem, self.upem)
        self.ft = freetype.Face(path)
        self._size = None

    def shape(self, text, size, tracking=0.0):
        ft = self.ft
        ft.set_char_size(int(round(size * 64)), 0, 72, 72)
        self._size = size
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(
            self.hb_font,
            buf,
            {
                "kern": True, "liga": True, "calt": True, "rlig": True,
                "curs": True, "mark": True, "mkmk": True, "ccmp": True,
            },
        )
        scale = size / self.upem
        return [
            (
                i.codepoint,
                p.x_advance * scale + tracking,
                p.y_advance * scale,
                p.x_offset * scale,
                p.y_offset * scale,
            )
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)
        ]


def measure(face, text, size, tracking=0.0):
    return sum(g[1] for g in face.shape(text, size, tracking))


WEAK_TAIL = {"و", "از", "با", "به", "که", "در", "یا"}


def break_lines(face, text, size, max_width, tracking=0.0):
    """Balanced ragged-left line breaking (slack-squared DP, last line free)."""
    words = text.split(" ")
    n = len(words)
    # width[i][j] : width of words i..j on one line
    width = [[0.0] * n for _ in range(n)]
    for i in range(n):
        w = ""
        for j in range(i, n):
            w = words[j] if not w else w + " " + words[j]
            width[i][j] = measure(face, w, size, tracking)

    INF = float("inf")
    best = [INF] * (n + 1)
    pre = [0] * (n + 1)
    best[0] = 0.0
    for i in range(1, n + 1):
        for j in range(0, i):
            wd = width[j][i - 1]
            if wd > max_width:
                continue
            slack = (max_width - wd) / max_width
            cost = slack ** 2.6            # strongly even ragging
            if words[i - 1] in WEAK_TAIL:
                cost += 0.10                # لا ينتهي السطر بحرف جر/عطف مفرد
            if i == n:                      # last line: softly penalise widows
                cost = 0.35 * slack ** 2
                if wd < 0.45 * max_width:
                    cost += 0.5
            if best[j] + cost < best[i]:
                best[i] = best[j] + cost
                pre[i] = j
    cuts, i = [], n
    while i > 0:
        cuts.append((pre[i], i))
        i = pre[i]
    cuts.reverse()
    return [" ".join(words[a:b]) for a, b in cuts]


# ----------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self):
        self.layers = []  # (mask, rgb, alpha)

    def draw_text(self, face, text, x, baseline, size, tracking=0.0, align="right"):
        glyphs = face.shape(text, size * SS, tracking)
        total = sum(g[1] for g in glyphs)
        pen = x * SS - total if align == "right" else x * SS - total / 2.0
        mask = np.zeros((H * SS, W * SS), dtype=np.float32)
        flags = freetype.FT_LOAD_RENDER
        base = baseline * SS
        for gid, adv, _, xoff, yoff in glyphs:
            face.ft.load_glyph(gid, flags)
            bmp = face.ft.glyph.bitmap
            w, h = bmp.width, bmp.rows
            if w and h:
                arr = np.array(bmp.buffer, dtype=np.float32).reshape(h, bmp.pitch)[:, :w]
                x0 = int(round(pen + xoff + face.ft.glyph.bitmap_left))
                y0 = int(round(base - yoff - face.ft.glyph.bitmap_top))
                x1, y1 = x0 + w, y0 + h
                if x1 > 0 and y1 > 0 and x0 < W * SS and y0 < H * SS:
                    sx0, sy0 = max(0, -x0), max(0, -y0)
                    dx0, dy0 = max(0, x0), max(0, y0)
                    dx1, dy1 = min(W * SS, x1), min(H * SS, y1)
                    src = arr[sy0 : sy0 + (dy1 - dy0), sx0 : sx0 + (dx1 - dx0)]
                    tgt = mask[dy0:dy1, dx0:dx1]
                    np.maximum(tgt, src / 255.0, out=tgt)
            pen += adv
        self.layers.append((mask, (0, 0, 0), 1.0))
        return len(self.layers) - 1

    def set_color(self, idx, rgb, alpha=1.0):
        m, _, _ = self.layers[idx]
        self.layers[idx] = (m, rgb, alpha)

    def hairline(self, x0, x1, y, thickness=1.0, alpha=1.0, rgb=HAIR_ACCENT):
        mask = np.zeros((H * SS, W * SS), dtype=np.float32)
        yy = int(round(y * SS))
        t = max(1, int(round(thickness * SS)))
        xa, xb = sorted((int(round(x0 * SS)), int(round(x1 * SS))))
        mask[yy : yy + t, xa:xb] = 1.0
        self.layers.append((mask, rgb, alpha))
        return len(self.layers) - 1

    def diamond(self, cx, cy, r, rgb=HAIR_ACCENT, alpha=1.0):
        mask = np.zeros((H * SS, W * SS), dtype=np.float32)
        # local window keeps memory small
        pad = int(np.ceil((r + 2) * SS))
        x0, y0 = int(cx * SS) - pad, int(cy * SS) - pad
        yy, xx = np.mgrid[0 : 2 * pad, 0 : 2 * pad].astype(np.float32)
        d = np.abs(xx - pad) + np.abs(yy - pad)
        m = np.clip((r * SS + 0.5) - d, 0, 1)
        mask[y0 : y0 + 2 * pad, x0 : x0 + 2 * pad] = m
        self.layers.append((mask, rgb, alpha))
        return len(self.layers) - 1


# ------------------------------------------------------------------ paper ----
def paper():
    """Warm ivory fine-art paper: three octaves of very low-amplitude, edge-free noise."""
    rng = np.random.default_rng(7)
    hh, ww = H, W
    fy = np.fft.fftfreq(hh)[:, None]
    fx = np.fft.rfftfreq(ww)[None, :]

    def smooth_noise(sigma, amp):
        white = rng.normal(0, 1, (hh, ww))
        spec = np.fft.rfft2(white) * np.exp(-2 * np.pi**2 * sigma**2 * (fx**2 + fy**2))
        out = np.fft.irfft2(spec, s=(hh, ww))
        out /= out.std()
        return (out * amp).astype(np.float32)

    texture = smooth_noise(40, 1.15) + smooth_noise(6.5, 0.45) + smooth_noise(0.9, 0.7)

    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    nx = (xx / ww - 0.5) * 2.0
    ny = (yy / hh - 0.5) * 2.0
    vig = 1.0 - 0.014 * np.clip(0.5 * nx**2 + 0.85 * ny**2, 0, 1)

    arr = np.zeros((hh, ww, 3), dtype=np.float32)
    for i, c in enumerate(PAPER):
        arr[:, :, i] = c
    arr += texture[:, :, None]
    arr *= vig[:, :, None]
    return np.clip(arr, 0, 255)


def compose(canvas, bg):
    out = bg.copy()
    for mask, rgb, alpha in canvas.layers:
        m = mask.reshape(H, SS, W, SS).mean(axis=(1, 3))
        m = np.clip(m, 0, 1)[:, :, None] * alpha
        col = np.array(rgb, dtype=np.float32)
        out = out * (1 - m) + col * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ----------------------------------------------------------------- layout ----
COL_RIGHT = 950
COL_LEFT = 130
COL_W = COL_RIGHT - COL_LEFT
ASC = 0.86  # baseline offset inside a line box (fraction of font size)

LIGHT = TypeFace("Vazirmatn-Light.ttf")
REG = TypeFace("Vazirmatn-Regular.ttf")
MED = TypeFace("Vazirmatn-Medium.ttf")
NASKH = TypeFace("NotoNaskhArabic-400.ttf")
NASKH_MED = TypeFace("NotoNaskhArabic-500.ttf")

BODY_SIZE = int(os.environ.get("BODY_SIZE", 45))
LEADING = int(os.environ.get("LEADING", 84))
PARA_GAP = 104

EYEBROW_Y = 205
MOTIF_Y = 268
BODY_TOP = 600
CLOSE_Y = 1380


def motif(c, y, span=34.0, gap=13.0, alpha=0.85):
    """Restrained hairline-and-diamond mark: — ◆ —"""
    c.hairline(W / 2 - gap - span, W / 2 - gap, y, 1.0, alpha, HAIR_ACCENT)
    c.hairline(W / 2 + gap, W / 2 + gap + span, y, 1.0, alpha, HAIR_ACCENT)
    c.diamond(W / 2, y + 0.5, 3.3, ACCENT, 0.9)


def top_marker(c, with_text):
    if with_text:
        i = c.draw_text(NASKH, BASMALA, W / 2, EYEBROW_Y + 6, 32, align="center")
        c.set_color(i, ACCENT, 0.95)
        motif(c, MOTIF_Y)
    else:
        motif(c, MOTIF_Y)


def story1():
    c = Canvas()
    bg = paper()
    top_marker(c, True)

    lines = break_lines(LIGHT, STORY1, BODY_SIZE, COL_W)
    top = BODY_TOP
    for i, line in enumerate(lines):
        idx = c.draw_text(LIGHT, line, COL_RIGHT, top + BODY_SIZE * ASC + i * LEADING, BODY_SIZE)
        c.set_color(idx, INK)

    motif(c, CLOSE_Y, span=40.0, gap=15.0, alpha=0.7)
    return compose(c, bg), lines


def story2():
    c = Canvas()
    bg = paper()
    top_marker(c, False)

    p1 = STORY2_P1_LINES
    p2 = STORY2_P2_LINES

    top = BODY_TOP
    y = top
    for i, line in enumerate(p1):
        idx = c.draw_text(LIGHT, line, COL_RIGHT, y + BODY_SIZE * ASC + i * LEADING, BODY_SIZE)
        c.set_color(idx, INK)
    y += (len(p1) - 1) * LEADING + BODY_SIZE + PARA_GAP
    for i, line in enumerate(p2):
        idx = c.draw_text(LIGHT, line, COL_RIGHT, y + BODY_SIZE * ASC + i * LEADING, BODY_SIZE)
        c.set_color(idx, INK)
    y += (len(p2) - 1) * LEADING + BODY_SIZE

    # signature: centred, with a short hairline above it
    rule_y = CLOSE_Y
    motif(c, rule_y, span=40.0, gap=15.0, alpha=0.7)
    i = c.draw_text(REG, SIGN_LEAD, W / 2, rule_y + 76, 27, align="center")
    c.set_color(i, ACCENT, 0.95)
    i = c.draw_text(NASKH, SIGN_NAME, W / 2, rule_y + 186, 68, align="center")
    c.set_color(i, INK_DEEP)
    return compose(c, bg), p1, p2


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    img1, l1 = story1()
    img2, p1, p2 = story2()
    img1.save(os.path.join(OUT, "story-01.png"))
    img2.save(os.path.join(OUT, "story-02.png"))

    for l in l1:
        print(f"S1 {measure(LIGHT, l, BODY_SIZE):6.1f}  {l}")
    print()
    for l in p1 + p2:
        print(f"S2 {measure(LIGHT, l, BODY_SIZE):6.1f}  {l}")
