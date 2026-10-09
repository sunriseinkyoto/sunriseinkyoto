#!/usr/bin/env python3
"""Reskin the generated Pac-Man graph: Luffy runs the maze, Marines and a pirate chase."""
import base64
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def uri(name):
    return "data:image/png;base64," + base64.b64encode((ASSETS / name).read_bytes()).decode()


SPRITES = {
    "luffy-right": uri("luffy.png"),
    "luffy-left": uri("luffy-left.png"),
    "marine-right": uri("marine.png"),
    "marine-left": uri("marine-left.png"),
    "pirate-right": uri("pirate.png"),
    "pirate-left": uri("pirate-left.png"),
    "meat": uri("meat.png"),
}

WHO = {"blinky": "marine", "inky": "marine", "pinky": "pirate", "clyde": "pirate"}


def swap_symbol(match):
    name, direction = match.group(1), match.group(2)
    side = "left" if direction == "left" else "right"
    href = SPRITES[f"{WHO[name]}-{side}"]
    return (
        f'<symbol id="ghost-{name}-{direction}" viewBox="0 0 20 20" overflow="visible">'
        f'<image href="{href}" x="-4" y="-6" width="28" height="28"/>'
    )


def swap_special(match):
    sid = match.group(1)
    return (
        f'<symbol id="{sid}" viewBox="0 0 20 20" overflow="visible">'
        f'<image href="{SPRITES["meat"]}" x="-2" y="-2" width="24" height="24"/>'
    )


def walls(svg):
    def repl(match):
        x, y, w, h = (int(match.group(i)) for i in range(1, 5))
        if h <= 3:
            y = max(0, y - 2)
            h = 6
        elif w <= 3:
            x = max(0, x - 2)
            w = 6
        return f'x="{x}" y="{y}" width="{w}" height="{h}" fill="#a97449" rx="1"'

    return re.sub(
        r'x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="#ffffff"',
        repl,
        svg,
    )


def pacman(svg):
    found = re.search(r"<path id=\"pacman\".*?</path>", svg, re.S)
    if not found:
        print("WARN: no pacman path")
        return svg
    block = found.group(0)
    trans = re.search(
        r'<animateTransform attributeName="transform" type="translate".*?/>', block, re.S
    ).group(0)
    rot = re.search(
        r'<animateTransform attributeName="transform" type="rotate".*?/>', block, re.S
    ).group(0)
    dur = re.search(r'dur="([^"]+)"', rot).group(1)
    times = re.search(r'keyTimes="([^"]+)"', rot).group(1)
    values = re.search(r'values="([^"]+)"', rot).group(1)
    angles = [int(float(v.split()[0])) % 360 for v in values.split(";")]
    right = ";".join("visible" if a in (0, 270) else "hidden" for a in angles)
    left = ";".join("hidden" if a in (0, 270) else "visible" for a in angles)
    first_right = "visible" if angles[0] in (0, 270) else "hidden"
    first_left = "hidden" if first_right == "visible" else "visible"

    def sprite(side, visible, vis):
        return (
            f'<image href="{SPRITES[side]}" x="-4" y="-6" width="28" height="28" visibility="{visible}">'
            f'<animate attributeName="visibility" dur="{dur}" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{times}" values="{vis}"/>'
            f'<animate attributeName="y" values="-6;-3;-6" dur="180ms" repeatCount="indefinite"/>'
            f"</image>"
        )

    group = f'<g id="pacman">{trans}{sprite("luffy-right", first_right, right)}{sprite("luffy-left", first_left, left)}</g>'
    return svg[: found.start()] + group + svg[found.end() :]


def theme(svg):
    svg, ghosts = re.subn(
        r'<symbol id="ghost-(blinky|inky|pinky|clyde)-(up|down|left|right)"[^>]*>\s*<image [^>]*>',
        swap_symbol,
        svg,
    )
    svg, specials = re.subn(
        r'<symbol id="(ghost-(?:scared|eyes-[a-z]+))"[^>]*>\s*<image [^>]*>',
        swap_special,
        svg,
    )
    svg = walls(pacman(svg))
    if not svg.startswith("<svg overflow"):
        svg = svg.replace("<svg ", '<svg overflow="visible" ', 1)
    print(f"ghosts {ghosts} specials {specials}")
    return svg


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    files = sorted(folder.glob("*.svg")) if folder.is_dir() else [folder]
    for path in files:
        path.write_text(theme(path.read_text(encoding="utf-8")), encoding="utf-8")
        print("themed", path)


if __name__ == "__main__":
    main()
