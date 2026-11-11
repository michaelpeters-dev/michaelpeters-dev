#!/usr/bin/env python3
"""Render the profile card shown on github.com/michaelpeters-dev.

Terminal output in the style of neofetch: two lines of text, then a row of
language tiles and a row of tool tiles. Writes assets/dark.svg and
assets/light.svg; README.md picks one by color scheme.

    python3 scripts/card.py

To change the text, edit INFO. To change the tiles, edit ROWS. Each icon's
outline and bounding box live in scripts/icons.json (Simple Icons, CC0).
The layout follows neofetch and Andrew Grant's profile card (github.com/Andrew6rant).
"""
import colorsys, json, os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INFO = [
    ("Host", "Georgia Tech · CS + Math · 2028"),
    ("Kernel", "Software Engineer Intern @ Ditto"),
]
ROWS = [
    ("Languages", ["rust", "cplusplus", "c", "x86", "python", "typescript", "javascript", "java", "swift", "kotlin"]),
    ("Tools", ["llvm", "webassembly", "qemu", "cmake", "sqlite", "docker", "aws", "git", "bash", "neovim"]),
]
ALT = ("Terminal output of neofetch for michael@gatech. Host: Georgia Tech, CS + Math, 2028. "
       "Kernel: Software Engineer Intern at Ditto. "
       "Languages: Rust, C++, C, x86 assembly, Python, TypeScript, JavaScript, Java, Swift, Kotlin. "
       "Tools: LLVM, WebAssembly, QEMU, CMake, SQLite, Docker, AWS, Git, Bash, Neovim.")

# Terminal grid: 14px monospace, 8.43px columns, 20px rows. The image is drawn
# only as wide as its content, so the README scales it up to the full column.
FS, CW, LH = 14, 8.43, 20
X0, VALUE_COL = 1.5, 12
TILE, GAP = 48, 12
# How much of its tile each icon fills (default 0.58); wide or thin marks get a little more.
FILL = {"rust": .62, "java": .62, "swift": .60, "kotlin": .42, "typescript": .60, "javascript": .52,
        "webassembly": .60, "llvm": .66, "docker": .66, "aws": .66}


def hsl(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


# The green is the avatar's: #68db95 = hsl(143, 61%, 63%). Light mode keeps the
# tiles that color and uses a darker shade of the same hue for text.
GREEN, HUE = "#68db95", 143
THEMES = {
    "dark": dict(text="#c9d1d9", dim="#8b949e", rule="#3d444d", accent=GREEN, tile=GREEN, ink="#0d1117"),
    "light": dict(text="#1f2328", dim="#6e7781", rule="#d0d7de", accent=hsl(HUE, 62, 27), tile=GREEN, ink=hsl(HUE, 60, 11)),
}


def tile(name, x, y, theme, icons):
    box = f'<rect x="{x:.1f}" y="{y}" width="{TILE}" height="{TILE}" rx="10" fill="{theme["tile"]}"/>'
    if name == "x86":   # no logo for assembly, so set it in the card's own type
        return box + (f'<text x="{x + TILE / 2:.1f}" y="{y + TILE / 2 + 6}" text-anchor="middle" textLength="33" '
                      f'lengthAdjust="spacingAndGlyphs" class="x">x86</text>')
    bx, by, bw, bh = icons[name]["box"]
    scale = TILE * FILL.get(name, .58) / max(bw, bh)
    tx = x + TILE / 2 - (bx + bw / 2) * scale
    ty = y + TILE / 2 - (by + bh / 2) * scale
    return box + (f'<path transform="translate({tx:.2f},{ty:.2f}) scale({scale:.4f})" '
                  f'fill="{theme["ink"]}" d="{icons[name]["d"]}"/>')


def build(theme, icons):
    prompt = '<tspan class="a">michael@gatech</tspan><tspan class="d">:~$</tspan>'
    xv = X0 + VALUE_COL * CW
    width = round(xv + max(len(names) for _, names in ROWS) * (TILE + GAP) - GAP + 2)

    y = 16
    out = [f'<text x="{X0}" y="{y}">{prompt} neofetch</text>']
    y += 2 * LH
    out.append(f'<text x="{X0}" y="{y}" class="a">michael@gatech</text>')
    out.append(f'<path d="M{X0} {y + LH - 5.5}h{14 * CW:.1f}" stroke="{theme["rule"]}"/>')
    y += 2 * LH
    for key, value in INFO:
        out.append(f'<text x="{X0}" y="{y}" class="a">{key}</text><text x="{xv:.1f}" y="{y}">{escape(value)}</text>')
        y += LH
    top = y - 2
    for label, names in ROWS:
        out.append(f'<text x="{X0}" y="{top + TILE / 2 + 5}" class="a">{label}</text>')
        out += [tile(name, xv + n * (TILE + GAP), top, theme, icons) for n, name in enumerate(names)]
        top += TILE + GAP
    y = top - GAP + LH + 14
    out.append(f'<text x="{X0}" y="{y}" textLength="{17 * CW:.1f}">{prompt}</text>')
    out.append(f'<rect class="c" x="{X0 + 18 * CW:.1f}" y="{y - 13}" width="{CW}" height="17" fill="{theme["text"]}"/>')
    height = y + 8

    css = ('text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;'
           f'font-size:{FS}px;fill:{theme["text"]};white-space:pre}}'
           f'.a{{fill:{theme["accent"]};font-weight:700}}.d{{fill:{theme["dim"]}}}'
           f'.x{{fill:{theme["ink"]};font-size:17px;font-weight:700}}'
           '.c{animation:c 1.1s steps(1) infinite}@keyframes c{50%{opacity:0}}'
           '@media (prefers-reduced-motion:reduce){.c{animation:none}}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(ALT)}">\n'
            f'<style>{css}</style>\n' + "\n".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    icons = json.load(open(os.path.join(ROOT, "scripts", "icons.json")))
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    for name, theme in THEMES.items():
        with open(os.path.join(ROOT, "assets", name + ".svg"), "w") as f:
            f.write(build(theme, icons))
