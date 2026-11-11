#!/usr/bin/env python3
"""Render the profile card: a spinning ASCII torus beside a neofetch-style readout.

Usage: GITHUB_TOKEN=... python3 scripts/card.py dist/card.svg
"""
import json, math, os, sys, urllib.request
from xml.sax.saxutils import escape

USER = "michaelpeters-dev"
COLS, ROWS, FRAMES, FPS = 40, 25, 48, 10
FS, ART_LH, LH = 14, 17, 21
W, PAD, INFO_X = 940, 26, 392


def stats():
    q = """{user(login:"%s"){followers{totalCount}
      repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount}}
      contributionsCollection{totalCommitContributions contributionCalendar{totalContributions}}}}""" % USER
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "User-Agent": "profile-card"},
    )
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    return dict(
        repos=u["repositories"]["totalCount"],
        stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        followers=u["followers"]["totalCount"],
        commits=u["contributionsCollection"]["totalCommitContributions"],
        contribs=u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    )


def torus(a, b):
    """One frame of a lit torus, rotated a about x and b about z."""
    shade = ".,-~:;=!*#$@"
    out = [[" "] * COLS for _ in range(ROWS)]
    zbuf = [[0.0] * COLS for _ in range(ROWS)]
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    r1, r2, k2 = 1.0, 2.0, 5.0
    k1 = COLS * k2 * 3 / (8 * (r1 + r2)) * 1.22
    t = 0.0
    while t < 2 * math.pi:
        ct, st = math.cos(t), math.sin(t)
        p = 0.0
        while p < 2 * math.pi:
            cp, sp = math.cos(p), math.sin(p)
            cx, cy = r2 + r1 * ct, r1 * st
            x = cx * (cb * cp + sa * sb * sp) - cy * ca * sb
            y = cx * (sb * cp - sa * cb * sp) + cy * ca * cb
            ooz = 1 / (k2 + ca * cx * sp + cy * sa)
            col = int(COLS / 2 + k1 * ooz * x)
            row = int(ROWS / 2 - k1 * ooz * y * 0.5)
            lum = cp * ct * sb - ca * ct * sp - sa * st + cb * (ca * st - ct * sa * sp)
            if 0 <= row < ROWS and 0 <= col < COLS and ooz > zbuf[row][col]:
                zbuf[row][col] = ooz
                out[row][col] = shade[max(0, int(lum * 8))]
            p += 0.02
        t += 0.07
    return ["".join(r).rstrip() for r in out]


def build(s):
    info = [
        ("h", "michael@gatech"),
        ("r", "─" * 14),
        ("kv", "Host", "Georgia Tech · B.S. CS, Math minor · 2028"),
        ("kv", "Kernel", "Software Engineer Intern @ Ditto"),
        ("kv", "Uptime", f"{s['contribs']:,} contributions in the last year"),
        ("kv", "Shell", "zsh + starship"),
        ("kv", "Editor", "Neovim"),
        ("kv", "WM", "AeroSpace + SketchyBar"),
        ("kv", "Terminal", "Ghostty"),
        ("b",),
        ("kv", "Languages", "Rust, C/C++, x86 asm, Python, TypeScript"),
        ("kv", "Systems", "MLIR/LLVM, WebAssembly, SIMD, Tokio, QEMU"),
        ("b",),
        ("kv", "Now.Ditto", "query engine + expression interpreter in Rust"),
        ("kv", "Now.TGT", "SIMD L2 order books, 1,660 → 870 µs"),
        ("kv", "Now.Tinker", "MLIR passes for the Qwerty quantum compiler"),
        ("kv", "Built", "StageZeroOS, an x86 OS from a 512-byte boot sector"),
        ("b",),
        ("kv", "GitHub", f"{s['repos']} public repos \u00b7 {s['commits']:,} commits this year"),
        ("kv", "Web", "michaelpeters.tech"),
    ]
    top = 76
    H = top + ROWS * ART_LH + 72
    dur = FRAMES / FPS
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal running neofetch for michael@gatech: systems engineer at Georgia Tech working in Rust, C++ and x86 assembly.">')
    o.append(f'''<defs>
<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{PAD}" y1="{top}" x2="{INFO_X - 30}" y2="{top + ROWS * ART_LH}">
<stop offset="0" stop-color="#ffa657"/><stop offset=".4" stop-color="#ff7b72"/><stop offset=".7" stop-color="#d2a8ff"/><stop offset="1" stop-color="#79c0ff"/>
</linearGradient>
<linearGradient id="t" x1="0" x2="1"><stop offset="0" stop-color="#ffa657"/><stop offset=".5" stop-color="#ff7b72"/><stop offset="1" stop-color="#d2a8ff"/></linearGradient>
</defs>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS}px;fill:#c9d1d9;white-space:pre}}
.f{{fill:url(#g);font-weight:700;opacity:0;animation:f {dur}s steps(1) infinite}}
@keyframes f{{0%{{opacity:1}}{100 / FRAMES:.4f}%{{opacity:0}}100%{{opacity:0}}}}
.l{{animation:i .5s ease-out backwards}}
@keyframes i{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:none}}}}
.k{{fill:#ffa657;font-weight:700}}.h{{fill:url(#t);font-weight:700}}.d{{fill:#8b949e}}.p{{fill:#7ee787}}
.c{{animation:b 1.1s steps(1) infinite}}
@keyframes b{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.f{{animation:none}}.f0{{opacity:1}}.l{{animation:none}}.c{{animation:none}}}}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<path d="M.5 38.5H{W - .5}" stroke="#30363d"/>
<circle cx="22" cy="19.5" r="6" fill="#ff5f57"/><circle cx="42" cy="19.5" r="6" fill="#febc2e"/><circle cx="62" cy="19.5" r="6" fill="#28c840"/>
<text x="{W / 2}" y="24" text-anchor="middle" class="d">michael@gatech: ~</text>
<text x="{PAD}" y="62"><tspan class="p">michael@gatech</tspan><tspan class="d">:</tspan><tspan fill="#79c0ff">~</tspan><tspan class="d">$</tspan> neofetch --ascii donut.c</text>''')
    for i in range(FRAMES):
        ang = 2 * math.pi * i / FRAMES
        rows = torus(1.0 + ang, ang)
        spans = "".join(
            f'<tspan x="{PAD}" y="{top + 12 + r * ART_LH}">{escape(line)}</tspan>' for r, line in enumerate(rows) if line
        )
        o.append(f'<text class="f f{i}" style="animation-delay:{-(dur - i / FPS) % dur:.2f}s">{spans}</text>')
    y = top + 14
    for n, row in enumerate(info):
        if row[0] != "b":
            if row[0] == "h":
                body = f'<tspan class="h">{row[1]}</tspan>'
            elif row[0] == "r":
                body = f'<tspan class="d">{row[1]}</tspan>'
            else:
                body = f'<tspan class="k">{row[1]:<12}</tspan>{escape(row[2])}'
            o.append(f'<text class="l" x="{INFO_X}" y="{y}" style="animation-delay:{0.25 + n * 0.07:.2f}s">{body}</text>')
        y += LH
    y += 4
    palette = ["#484f58", "#ff7b72", "#7ee787", "#ffa657", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"]
    blocks = "".join(f'<rect x="{INFO_X + j * 30}" y="{y - 14}" width="30" height="18" fill="{c}"/>' for j, c in enumerate(palette))
    o.append(f'<g class="l" style="animation-delay:{0.25 + len(info) * 0.07:.2f}s">{blocks}</g>')
    py = H - 18
    o.append(f'<text x="{INFO_X}" y="{py}"><tspan class="p">michael@gatech</tspan><tspan class="d">:</tspan><tspan fill="#79c0ff">~</tspan><tspan class="d">$</tspan></text>')
    o.append(f'<rect class="c" x="{INFO_X + 152}" y="{py - 14}" width="9" height="18" fill="#c9d1d9"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    dest = sys.argv[1]
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    open(dest, "w").write(build(stats()))
