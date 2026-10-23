"""Build Kamphaeng-Regular.ttf / .woff2.

Lao: Noto Sans Lao Black's layout tables (GSUB alternates, GPOS mark/mkmk/kern) kept as-is,
     outlines replaced from sources/Kamphaeng-Regular.ufo (the design source edited in FontLab).
Latin: Black Ops One, scaled to 1000 UPM. Merged with fontTools.merge.
"""
import json
import tempfile
from pathlib import Path

import ufoLib2
from fontTools import subset
from fontTools.merge import Merger
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from lib import BASE, LATIN, ROOT, lao_glyph_names, tt_glyph

UFO = ROOT / "sources/Kamphaeng-Regular.ufo"
OUT = ROOT / "fonts"
LAO_UNICODES = list(range(0x0E80, 0x0F00)) + [0x25CC, 0x200B, 0x200C, 0x200D]
LATIN_UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + list(range(0x2010, 0x203B))
                  + [0x20AC, 0x20AD, 0x2122, 0x2212])


def _subset(font: TTFont, unicodes, keep_names=True) -> TTFont:
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.glyph_names = keep_names
    opts.notdef_outline = True
    opts.hinting = False
    opts.drop_tables += ["DSIG", "gasp", "STAT", "fvar", "gvar", "avar", "HVAR", "MVAR"]
    s = subset.Subsetter(opts)
    s.populate(unicodes=unicodes)
    s.subset(font)
    return font


def lao_part(tmp: Path) -> Path:
    tt = TTFont(BASE)
    ufo = ufoLib2.Font.open(UFO)
    names = lao_glyph_names(tt)
    glyf, hmtx = tt["glyf"], tt["hmtx"]
    for name in names:
        if name not in ufo:
            continue
        g = ufo[name]
        contours = [[{"x": p.x, "y": p.y, "type": p.type or "offcurve"} for p in c] for c in g]
        glyf[name] = tt_glyph(contours)
        glyf[name].recalcBounds(glyf)
        hmtx[name] = (int(round(g.width)), getattr(glyf[name], "xMin", 0) if contours else 0)
    _subset(tt, LAO_UNICODES)
    p = tmp / "lao.ttf"
    tt.save(p)
    return p


def latin_part(tmp: Path) -> Path:
    tt = TTFont(LATIN)
    scale_upem(tt, 1000)
    _subset(tt, LATIN_UNICODES)
    p = tmp / "latin.ttf"
    tt.save(p)
    return p


def finish(tt: TTFont, ufo: ufoLib2.Font):
    i = ufo.info
    version = f"{i.versionMajor}.{i.versionMinor:03d}"
    name = tt["name"]
    name.names = []
    fam = i.familyName
    for nid, val in {0: i.copyright, 1: fam, 2: "Regular", 3: f"{version};NONE;{fam.replace(' ', '')}-Regular",
                     4: f"{fam} Regular", 5: f"Version {version}", 6: f"{fam.replace(' ', '')}-Regular",
                     9: i.openTypeNameDesigner, 13: i.openTypeNameLicense, 14: i.openTypeNameLicenseURL,
                     19: "ສະບາຍດີ ພາສາລາວ — BLACK OPS ONE"}.items():
        name.setName(val, nid, 3, 1, 0x409)
    tt["head"].fontRevision = float(version)
    # vertical metrics from the real extents, so stacked Lao marks never clip
    glyf = tt["glyf"]
    ymax = max(getattr(glyf[g], "yMax", 0) for g in tt.getGlyphOrder())
    ymin = min(getattr(glyf[g], "yMin", 0) for g in tt.getGlyphOrder())
    os2, hhea = tt["OS/2"], tt["hhea"]
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = 1000, -350, 0
    os2.usWinAscent, os2.usWinDescent = max(ymax, 1000), max(-ymin, 350)
    hhea.ascent, hhea.descent, hhea.lineGap = os2.usWinAscent, -os2.usWinDescent, 0
    os2.fsSelection |= 1 << 7  # USE_TYPO_METRICS
    os2.usWeightClass = 900
    os2.achVendID = "NONE"
    tt["post"].formatType = 2.0


def build():
    OUT.mkdir(exist_ok=True)
    ufo = ufoLib2.Font.open(UFO)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        latin, lao = latin_part(d), lao_part(d)
        merged = Merger().merge([str(latin), str(lao)])
    finish(merged, ufo)
    ttf = OUT / "Kamphaeng-Regular.ttf"
    merged.save(ttf)
    w = TTFont(ttf)
    w.flavor = "woff2"
    w.save(OUT / "Kamphaeng-Regular.woff2")
    return {"ttf": str(ttf), "glyphs": len(merged.getGlyphOrder()),
            "scripts": sorted({s.ScriptTag for s in merged["GPOS"].table.ScriptList.ScriptRecord})}


if __name__ == "__main__":
    print(json.dumps(build()))
