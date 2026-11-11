#!/usr/bin/env python3
"""Render the profile card shown on github.com/michaelpeters-dev.

One terminal screen on a 100-column grid: a spinning ASCII torus beside a
neofetch-style readout. Writes assets/dark.svg and assets/light.svg; README.md
picks one by color scheme.

The torus math is Andy Sloane's donut.c. The art-plus-readout layout follows
neofetch and Andrew Grant's profile card (github.com/Andrew6rant).

    python3 scripts/card.py             rebuild both files
    python3 scripts/card.py --frame 6   one static frame, for previewing

To change the text, edit INFO. To change the icons, edit TILES; their path
data lives in scripts/icons.json (Simple Icons, CC0).
"""
import argparse, colorsys, json, math, os, re
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Terminal grid: 14px monospace, 8.43px columns, 18px rows.
FS, CW, LH = 14, 8.43, 18
W, X0, PAD_TOP = 846, 1.5, 2       # 846px is the README column width on a profile
DONUT_COLS, DONUT_ROWS = 40, 20
FRAMES, LOOP = 64, 4.8             # 64 frames in 4.8s: 0.075s each, 1.5625% of the loop
INFO_COL, VALUE_COL = 44, 56
TILE, TILE_GAP = 36, 8

SHADE = ".,-~:;=!*#$@"                         # dark to bright, as in donut.c
TONE = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 3, 3]    # which of four greens each character gets

INFO = [
    ("Host", "Georgia Tech · CS + Math · 2028"),
    ("Kernel", "Software Engineer Intern @ Ditto"),
    ("Systems", "MLIR/LLVM, WebAssembly, SIMD, QEMU"),
    None,
    ("Now.Ditto", "query engine + interpreter in Rust"),
    ("Now.TGT", "SIMD L2 order books, 1,660 → 870 µs"),
    ("Now.Tinker", "Qwerty quantum compiler on MLIR/LLVM"),
    None,
]
TILES = ["rust", "cplusplus", "c", "x86", "python", "typescript", "swift", "kotlin"]
ALT = ("Terminal output of neofetch for michael@gatech beside a spinning ASCII donut. "
       "Host: Georgia Tech, CS + Math, 2028. Kernel: Software Engineer Intern at Ditto. "
       "Systems: MLIR/LLVM, WebAssembly, SIMD, QEMU. Now at Ditto: query engine and interpreter in Rust. "
       "Now at TGT: SIMD L2 order books, 1,660 to 870 microseconds. Now at Tinker Lab: Qwerty quantum compiler on MLIR/LLVM. "
       "Languages: Rust, C++, C, x86 assembly, Python, TypeScript, Swift, Kotlin.")


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


# Everything green is one hue, taken from the avatar: #68db95 = hsl(143, 61%, 63%).
GREEN, HUE = "#68db95", 143
THEMES = {
    "dark": dict(text="#c9d1d9", dim="#8b949e", rule="#3d444d", accent=GREEN, tile=GREEN, ink="#0d1117",
                 tones=[hsl(HUE, 38, 30), hsl(HUE, 50, 46), GREEN, hsl(HUE, 85, 82)]),
    "light": dict(text="#1f2328", dim="#6e7781", rule="#d0d7de", accent=hsl(HUE, 62, 27), tile=GREEN, ink=hsl(HUE, 60, 11),
                  tones=[hsl(HUE, 40, 72), hsl(HUE, 48, 52), hsl(HUE, 58, 37), hsl(HUE, 66, 24)]),
}


def torus_points(a, b, k2=5.0):
    """Points on a torus rotated a about x and b about z, as (x/z, y/z, 1/z, brightness)."""
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    out = []
    for i in range(90):
        t = i * 2 * math.pi / 90
        ct, st = math.cos(t), math.sin(t)
        cx, cy = 2 + ct, st
        for j in range(314):
            p = j * 2 * math.pi / 314
            cp, sp = math.cos(p), math.sin(p)
            ooz = 1 / (k2 + ca * cx * sp + cy * sa)
            x = cx * (cb * cp + sa * sb * sp) - cy * ca * sb
            y = cx * (sb * cp - sa * cb * sp) + cy * ca * cb
            lum = cp * ct * sb - ca * ct * sp - sa * st + cb * (ca * st - ct * sa * sp)
            out.append((x * ooz, y * ooz, ooz, lum))
    return out


def donut_frames():
    """Each frame as a DONUT_ROWS x DONUT_COLS grid of SHADE indexes (-1 where empty)."""
    spin = [2 * math.pi * i / FRAMES for i in range(FRAMES)]
    clouds = [torus_points(1.6 + s, 0.6 + s) for s in spin]   # frame 0 is the classic three-quarter view
    # Scale so the widest and tallest frame of the whole loop still fits the grid.
    widest = max(abs(p[0]) for c in clouds for p in c)
    tallest = max(abs(p[1]) for c in clouds for p in c)
    k1 = min((DONUT_COLS / 2 - 0.6) / widest, (DONUT_ROWS / 2 - 0.6) / (tallest * CW / LH))
    frames = []
    for cloud in clouds:
        grid = [[-1] * DONUT_COLS for _ in range(DONUT_ROWS)]
        depth = [[0.0] * DONUT_COLS for _ in range(DONUT_ROWS)]
        for x, y, ooz, lum in cloud:
            c = math.floor(DONUT_COLS / 2 + k1 * x)
            r = math.floor(DONUT_ROWS / 2 - k1 * y * CW / LH)
            if 0 <= r < DONUT_ROWS and 0 <= c < DONUT_COLS and ooz > depth[r][c]:
                depth[r][c] = ooz
                grid[r][c] = max(0, int(lum * 8))
        frames.append(grid)
    return frames


def inner_glyph(d):
    """Drop the first subpath (the square around a 'logo in a square' icon), keeping what is inside."""
    start = re.match(r"M\s*(-?\d*\.?\d+)[\s,]*(-?\d*\.?\d+)", d)
    end = re.search(r"z", d, re.I).end()
    move = re.match(r"\s*m\s*(-?\d*\.?\d+)[\s,]*(-?\d*\.?\d+)", d[end:])
    x, y = float(start.group(1)) + float(move.group(1)), float(start.group(2)) + float(move.group(2))
    return f"M{x:g} {y:g}" + d[end + move.end():]


def tile(name, x, y, theme, icons):
    box = f'<rect x="{x:.1f}" y="{y}" width="{TILE}" height="{TILE}" rx="8" fill="{theme["tile"]}"/>'
    if name == "x86":
        return box + (f'<text x="{x + TILE / 2:.1f}" y="{y + TILE / 2 + 4.6:.1f}" text-anchor="middle" textLength="25" '
                      f'lengthAdjust="spacingAndGlyphs" class="x">x86</text>')
    d, size, dx, dy = icons[name], 21, 0.0, 0.0
    if name == "rust":
        size = 22
    elif name == "kotlin":
        size = 16
    elif name == "swift":
        d, size = inner_glyph(d), 25
    elif name == "typescript":
        # The letters sit bottom-right in the logo; centre them in the tile instead.
        d, size = inner_glyph(d), 26
        dx, dy = (12 - 12.99) * size / 24, (12 - 15.83) * size / 24
    off = (TILE - size) / 2
    return box + (f'<path transform="translate({x + off + dx:.2f},{y + off + dy:.2f}) scale({size / 24:.4f})" '
                  f'fill="{theme["ink"]}" d="{d}"/>')


def build(theme, frames, icons, still=None):
    rows = DONUT_ROWS + 4                      # prompt, blank, donut, blank, prompt
    height = PAD_TOP + rows * LH + 4
    baseline = lambda row: PAD_TOP + row * LH + 13
    prompt = '<tspan class="a">michael@gatech</tspan><tspan class="d">:~$</tspan>'
    css = [
        'text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;'
        f'font-size:{FS}px;fill:{theme["text"]};white-space:pre}}',
        f'.a{{fill:{theme["accent"]};font-weight:700}}.d{{fill:{theme["dim"]}}}',
        f'.x{{fill:{theme["ink"]};font-size:13px;font-weight:700}}',
    ]
    css += [f'.t{n}{{fill:{c};font-weight:700}}' for n, c in enumerate(theme["tones"])]
    if still is None:
        css += [
            f'.f{{opacity:0;animation:f {LOOP}s steps(1) infinite}}',
            f'@keyframes f{{0%{{opacity:1}}{100 / FRAMES:g}%{{opacity:0}}100%{{opacity:0}}}}',
            '.c{animation:c 1.1s steps(1) infinite}@keyframes c{50%{opacity:0}}',
            '@media (prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}.c{animation:none}}',
        ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="{escape(ALT)}">',
        "<style>" + "".join(css) + "</style>",
        f'<text x="{X0}" y="{baseline(0)}">{prompt} neofetch</text>',
    ]

    # Donut: one group per frame, each frame split into four tone layers.
    for i, grid in enumerate(frames):
        if still is not None and i != still:
            continue
        layers = []
        for tone in range(4):
            spans = []
            for r, row in enumerate(grid):
                line = "".join(SHADE[v] if v >= 0 and TONE[v] == tone else " " for v in row).rstrip()
                if line:
                    spans.append(f'<tspan x="{X0}" y="{baseline(2 + r)}">{escape(line)}</tspan>')
            if spans:
                layers.append(f'<text class="t{tone}">{"".join(spans)}</text>')
        attrs = "" if still is not None else f' class="f f{i}" style="animation-delay:{i * LOOP / FRAMES:g}s"'
        out.append(f"<g{attrs}>{''.join(layers)}</g>")

    # Readout, centred against the donut.
    xi, xv = X0 + INFO_COL * CW, X0 + VALUE_COL * CW
    row = 2 + (DONUT_ROWS - (2 + len(INFO) + 2)) // 2
    out.append(f'<text x="{xi:.1f}" y="{baseline(row)}" class="a">michael@gatech</text>')
    out.append(f'<path d="M{xi:.1f} {baseline(row + 1) - 4.5}h{14 * CW:.1f}" stroke="{theme["rule"]}"/>')
    row += 2
    for item in INFO:
        if item:
            out.append(f'<text x="{xi:.1f}" y="{baseline(row)}" class="a">{item[0]}</text>'
                       f'<text x="{xv:.1f}" y="{baseline(row)}">{escape(item[1])}</text>')
        row += 1
    top = PAD_TOP + row * LH
    out.append(f'<text x="{xi:.1f}" y="{top + TILE / 2 + 5}" class="a">Languages</text>')
    out += [tile(name, xv + n * (TILE + TILE_GAP), top, theme, icons) for n, name in enumerate(TILES)]

    # Closing prompt and cursor.
    y = baseline(rows - 1)
    out.append(f'<text x="{X0}" y="{y}" textLength="{17 * CW:.1f}">{prompt}</text>')
    out.append(f'<rect class="c" x="{X0 + 18 * CW:.1f}" y="{y - 13}" width="{CW}" height="17" fill="{theme["text"]}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frame", type=int, help="render only this frame, without animation")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets"))
    args = ap.parse_args()
    icons = json.load(open(os.path.join(ROOT, "scripts", "icons.json")))
    frames = donut_frames()
    os.makedirs(args.out, exist_ok=True)
    for name, theme in THEMES.items():
        with open(os.path.join(args.out, name + ".svg"), "w") as f:
            f.write(build(theme, frames, icons, args.frame))
