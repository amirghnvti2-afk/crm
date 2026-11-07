# استوری‌های یادبود و قدردانی — خانواده قنواتی
## Qanavati family — tribute story pair (1080 × 1920)

Two independent Instagram / WhatsApp story images, drawn from a single visual system.

| file | content |
| --- | --- |
| `out/story-01.png` | بسمه‌تعالی + پیام سپاسگزاری |
| `out/story-02.png` | ادامه پیام + دعای خیر + امضای «خانواده قنواتی» |

### Design system

* **Palette** — paper `#F8F4EB` (warm ivory, fine-art paper), ink `#23221E` (soft
  charcoal), accent `#74807A` (muted blue-green), hairlines `#9AA29C` / `#DCD5C6`.
* **Type** — body: *Vazirmatn Light* 45 px / 84 px leading, right-aligned ragged-left
  column 820 px wide (right edge at x 950, left at x 130). Eyebrow and signature:
  *Noto Naskh Arabic* (400 / 500) — a classical naskh counterpoint that gives the
  opening «بسمه‌تعالی» and the signature a ceremonial, printed feel.
* **Grid** — shared vertical anchors across both cards: eyebrow baseline 205,
  motif 268, body first baseline 645, closing motif / signature mark 1380.
  All content stays ≥ 90 px from every edge (measured: 132–266 px).
* **Ornament** — one restrained mark only (`— ◆ —`, 1 px hairline + 6 px diamond),
  used as the top marker on both cards and as the signature mark on card two.
* **Paper** — three octaves of edge-free spectral noise (σ = 40 / 6.5 / 0.9 px) at
  ±1.5 gray levels plus a 1.4 % vignette: texture that reads as paper, never as noise.

### Craft notes

* Persian is shaped by **HarfBuzz** (liga / calt / rlig / curs / mark / mkmk / ccmp)
  and rasterised by **FreeType** with hinting at **2× supersampling**, then downsampled —
  so every letter joins correctly and the copy is reproduced character-for-character.
* Line breaks are set by a slack-squared dynamic programme with weak-tail penalties
  (no line ends on a bare «و / از / با»), and the short paragraphs are hand-broken.
  `بسمه‌تعالی` appears exactly once, on card one only.
* No extra copy, watermark, logo or signature-by-designer was added.

### Rebuild

```bash
pip install pillow numpy uharfbuzz freetype-py
python3 build.py            # writes out/story-01.png, out/story-02.png
```

Fonts (SIL OFL) live in `fonts/`: Vazirmatn Light/Regular/Medium/SemiBold,
Noto Naskh Arabic 400–700.
