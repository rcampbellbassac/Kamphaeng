"""Shared helpers for the Kamphaeng build (runs in ~/Source/fontlab-mcp/.venv on xray)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # vendored fontlab_mcp
from fontTools.pens.cu2quPen import Cu2QuPen  # noqa: E402
from fontTools.pens.ttGlyphPen import TTGlyphPen  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from fontlab_mcp import offline, stylize  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REFS = Path.home() / "Fonts/reference"
BASE_VF = REFS / "lao/google/notosanslao/NotoSansLao[wdth,wght].ttf"
BASE = ROOT / "base/NotoSansLao-Black.ttf"
LATIN = REFS / "google/blackopsone/BlackOpsOne-Regular.ttf"


def fetch_references():
    """Download Noto Sans Lao and Black Ops One from github.com/google/fonts if missing."""
    if not BASE_VF.exists():
        offline.google_fonts_fetch("Noto Sans Lao", BASE_VF.parent)
    if not LATIN.exists():
        offline.google_fonts_fetch("Black Ops One", LATIN.parent)


def lao_glyph_names(tt: TTFont) -> list[str]:
    """Lao-script glyphs: cmap'd Lao codepoints plus unmapped alternates/ligatures reachable from them."""
    cmap = tt.getBestCmap()
    names = {g for cp, g in cmap.items() if 0x0E80 <= cp <= 0x0EFF}
    mapped = set(cmap.values())
    for g in tt.getGlyphOrder():
        if g not in mapped and g != ".notdef" and ("0E" in g or "lao" in g.lower()):
            names.add(g)
    names.add("uni25CC")  # dotted circle, used for isolated marks
    return [g for g in tt.getGlyphOrder() if g in names]


def contours_from_tt(tt: TTFont, name: str) -> list[list[dict]]:
    pen = offline._UFOPointCollector(tt.getGlyphSet())
    tt.getGlyphSet()[name].draw(pen)
    return pen.contours


def tt_glyph(contours, glyphset=None):
    """UFO point contours (lines/cubics) -> TrueType glyf glyph (cubics converted with cu2qu)."""
    pen = TTGlyphPen(glyphset)
    qpen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
    for c in contours:
        pts = c
        first_on = next(i for i, p in enumerate(pts) if p["type"] != "offcurve")
        pts = pts[first_on:] + pts[:first_on]
        qpen.moveTo((pts[0]["x"], pts[0]["y"]))
        offs = []
        for p in pts[1:] + [pts[0]]:
            if p["type"] == "offcurve":
                offs.append((p["x"], p["y"]))
            elif p["type"] == "curve":
                qpen.curveTo(*offs, (p["x"], p["y"]))
                offs = []
            else:
                qpen.lineTo((p["x"], p["y"]))
        qpen.closePath()
    return pen.glyph()
