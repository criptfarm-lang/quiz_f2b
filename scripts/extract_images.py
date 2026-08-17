#!/usr/bin/env python3
"""Вынос base64-картинок из course_f2b.html в отдельные файлы img/.

Причина: файл 8,1 МБ, 96,5% — картинки в base64. Браузер обязан скачать всё
целиком до первой отрисовки → на рабочем компьютере курс «висит».
После выноса: HTML ~300 КБ, картинки грузятся лениво, по мере открытия уроков.

Формат определяем по сигнатуре байтов (Pillow), а не по mime в data-URI —
там половина «image/png» на деле JPEG.
"""
import base64
import io
import os
import re
import sys

from PIL import Image

SRC = os.path.expanduser("~/code/quiz_f2b/course_f2b.html")
IMGDIR = os.path.expanduser("~/code/quiz_f2b/img")
MAX_W = 1400          # шире не нужно: карточка урока max ~900 CSS px, запас на retina
WEBP_Q = 82

os.makedirs(IMGDIR, exist_ok=True)
html = open(SRC, encoding="utf-8").read()
orig_len = len(html)

pat = re.compile(r'<img([^>]*?)src="data:image/[a-zA-Z+]+;base64,([A-Za-z0-9+/=]+)"([^>]*?)>')

stats = []
counter = [0]


def repl(m):
    before, b64, after = m.group(1), m.group(2), m.group(3)
    raw = base64.b64decode(b64)
    counter[0] += 1
    idx = counter[0]
    im = Image.open(io.BytesIO(raw))
    fmt_in = im.format
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")
    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    name = f"l{idx:03d}.webp"
    path = os.path.join(IMGDIR, name)
    im.save(path, "WEBP", quality=WEBP_Q, method=6)
    new_size = os.path.getsize(path)
    stats.append((name, fmt_in, len(raw), new_size))

    attrs = (before + after).strip()
    # первая картинка — шапка главной, она видна сразу: без lazy
    lazy = "" if idx == 1 else ' loading="lazy" decoding="async"'
    sep = " " if attrs else ""
    return f'<img{sep}{attrs} src="img/{name}"{lazy}>'


html = pat.sub(repl, html)

left = len(re.findall(r"data:image/", html))
if left:
    print(f"ВНИМАНИЕ: осталось {left} невынесенных data:image/ вхождений", file=sys.stderr)

open(SRC, "w", encoding="utf-8").write(html)

old_total = sum(s[2] for s in stats)
new_total = sum(s[3] for s in stats)
print(f"картинок вынесено: {len(stats)}")
print(f"HTML: {orig_len/1024/1024:.2f} МБ → {len(html)/1024:.0f} КБ")
print(f"картинки: {old_total/1024/1024:.2f} МБ → {new_total/1024/1024:.2f} МБ (в img/)")
print(f"итого при первой загрузке страницы: {len(html)/1024:.0f} КБ вместо {orig_len/1024/1024:.2f} МБ")
