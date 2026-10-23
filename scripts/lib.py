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


# ---------------------------------------------------------------- Thai and Khmer (added 0.200)

SCRIPTS = {
    "lao": {"vf": BASE_VF, "base": BASE, "ufo": ROOT / "sources/Kamphaeng-Regular.ufo",
            "unicodes": list(range(0x0E80, 0x0F00)) + [0x25CC, 0x200B, 0x200C, 0x200D]},
    "thai": {"vf": REFS / "google-base/notosansthai/NotoSansThai[wdth,wght].ttf", "base": ROOT / "base/NotoSansThai-Black-sub.ttf",
             "ufo": ROOT / "sources/Kamphaeng-Thai.ufo", "unicodes": list(range(0x0E01, 0x0E5C)) + [0x25CC, 0x200B, 0x200C, 0x200D]},
    "khmer": {"vf": REFS / "google-base/notosanskhmer/NotoSansKhmer[wdth,wght].ttf", "base": ROOT / "base/NotoSansKhmer-Black-sub.ttf",
              "ufo": ROOT / "sources/Kamphaeng-Khmer.ufo",
              "unicodes": list(range(0x1780, 0x1800)) + list(range(0x19E0, 0x1A00)) + [0x25CC, 0x200B, 0x200C, 0x200D]},
}


def subset_layout(font: TTFont, unicodes) -> TTFont:
    from fontTools import subset
    o = subset.Options()
    o.layout_features = ["*"]; o.name_IDs = ["*"]; o.glyph_names = True; o.notdef_outline = True; o.hinting = False
    o.drop_tables += ["DSIG", "gasp", "STAT", "fvar", "gvar", "avar", "HVAR", "MVAR", "vhea", "vmtx"]
    s = subset.Subsetter(o); s.populate(unicodes=unicodes); s.subset(font)
    return font


def ensure_script_base(script: str) -> Path:
    """Black (wght 900) instance of the script's Noto font, subset to that script with its layout tables."""
    from fontTools.varLib import instancer
    cfg = SCRIPTS[script]
    if script == "lao":
        return cfg["base"]
    if not cfg["vf"].exists():
        fam = {"thai": "Noto Sans Thai", "khmer": "Noto Sans Khmer"}[script]
        offline.google_fonts_fetch(fam, cfg["vf"].parent)
    if not cfg["base"].exists():
        cfg["base"].parent.mkdir(parents=True, exist_ok=True)
        tt = instancer.instantiateVariableFont(TTFont(cfg["vf"]), {"wght": 900, "wdth": 100})
        subset_layout(tt, cfg["unicodes"]).save(cfg["base"])
    return cfg["base"]


def script_glyph_names(tt: TTFont, script: str) -> list[str]:
    if script == "lao":
        return lao_glyph_names(tt)
    skip = {".notdef", "space", "uni00A0", "NULL", "CR", "uni200B", "uni200C", "uni200D"}
    return [g for g in tt.getGlyphOrder() if g not in skip]
