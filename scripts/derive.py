"""Derive / refresh the Kamphaeng design source (UFO) from Noto Sans Lao Black.

  python derive.py                 regenerate every glyph that is not locked
  python derive.py uni0E81 ...     regenerate only these (still skips locked ones unless --force)
  python derive.py --script=thai   Thai (sources/Kamphaeng-Thai.ufo); --script=khmer for Khmer

Per-glyph design decisions live in design/overrides.json:
  {"uni0E94": {"cuts": [{"x0":..,"y0":..,"x1":..,"y1":..}], "auto": false, "eps": 12}}
  cuts: extra stencil gaps; auto: false disables the automatic gaps; eps: simplification tolerance;
  junctions: max automatic junction gaps (0 = none); bold: extra stem weight per side (units).
Spacing glyphs widen by 2*bold and shift right by bold; the shift is stored in the UFO lib key
"kamphaeng.xshift" so build.py moves the GPOS mark anchors by the same amount.
Glyphs hand-edited in FontLab are listed in the UFO lib key "kamphaeng.locked" and never regenerated.
"""
import json
import sys

import ufoLib2
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from lib import BASE, BASE_VF, ROOT, SCRIPTS, contours_from_tt, ensure_script_base, fetch_references, lao_glyph_names, script_glyph_names, stylize

UFO = ROOT / "sources/Kamphaeng-Regular.ufo"
OVERRIDES = ROOT / "design/overrides.json"
DEFAULTS = {"eps": 16.0, "min_edge": 10.0, "gap": 22.0, "junctions": 2, "bold": 14.0}


def ensure_base():
    fetch_references()
    if not BASE.exists():
        BASE.parent.mkdir(parents=True, exist_ok=True)
        instancer.instantiateVariableFont(TTFont(BASE_VF), {"wght": 900, "wdth": 100}).save(BASE)


def new_ufo():
    f = ufoLib2.Font()
    i = f.info
    i.familyName, i.styleName = "Kamphaeng", "Regular"
    i.unitsPerEm, i.ascender, i.descender, i.xHeight, i.capHeight = 1000, 900, -350, 519, 648
    i.versionMajor, i.versionMinor = 0, 100
    i.copyright = ("Copyright 2026 Robert Martin Campbell. Lao outlines derived from Noto Sans Lao "
                   "(Copyright 2022 The Noto Project Authors); Latin from Black Ops One "
                   "(Copyright 2022 The Black-Ops Project Authors).")
    i.openTypeNameDesigner = "Robert Martin Campbell"
    i.openTypeNameLicense = "This Font Software is licensed under the SIL Open Font License, Version 1.1."
    i.openTypeNameLicenseURL = "https://openfontlicense.org"
    f.lib["kamphaeng.locked"] = []
    return f


def derive(only=None, force=False, script="lao"):
    ensure_base()
    base = ensure_script_base(script)
    UFO = SCRIPTS[script]["ufo"]
    tt = TTFont(base)
    cmap = {g: cp for cp, g in tt.getBestCmap().items()}
    overrides = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    ufo = ufoLib2.Font.open(UFO) if UFO.exists() else new_ufo()
    locked = set(ufo.lib.get("kamphaeng.locked", []))
    report = {"derived": 0, "skipped_locked": [], "cuts": {}}
    for name in script_glyph_names(tt, script):
        if only and name not in only:
            continue
        if name in locked and not force:
            report["skipped_locked"].append(name)
            continue
        o = {**DEFAULTS, **overrides.get(name, {})}
        src = contours_from_tt(tt, name)
        outl = stylize.octilinearize(src, eps=o["eps"], min_edge=o["min_edge"]) if src else []
        width = tt["hmtx"][name][0]
        shift = 0.0
        if outl and o["bold"]:
            outl = stylize.embolden_x(outl, o["bold"])
            if width > 0:  # spacing glyph: keep sidebearings, widen the advance
                shift = o["bold"]
                outl = stylize.translate(outl, shift)
                width += 2 * o["bold"]
        cuts = list(o.get("cuts", []))
        if outl and o.get("auto", True):
            cuts = stylize.auto_stencil_cuts(outl, gap=o["gap"]) + cuts
            if o["junctions"]:
                holed = stylize.stencil_cut(outl, cuts) if cuts else outl
                cuts += stylize.auto_junction_cuts(holed, gap=o["gap"], max_cuts=o["junctions"])
        if outl and cuts:
            outl = stylize.clean_overlaps(stylize.stencil_cut(outl, cuts))
            report["cuts"][name] = len(cuts)
        g = ufo.get(name) or ufo.newGlyph(name)
        g.clearContours()
        g.width = width
        ufo.lib.setdefault("kamphaeng.xshift", {})[name] = shift
        g.unicodes = [cmap[name]] if name in cmap else []
        pen = g.getPointPen()
        for c in outl:
            pen.beginPath()
            for p in c:
                pen.addPoint((p["x"], p["y"]), segmentType=p["type"] if p["type"] != "offcurve" else None)
            pen.endPath()
        report["derived"] += 1
    # keep glyph order = Noto order for the layout tables
    ufo.lib["public.glyphOrder"] = [g for g in tt.getGlyphOrder() if g in ufo]
    UFO.parent.mkdir(parents=True, exist_ok=True)
    ufo.save(UFO, overwrite=True)
    return report


if __name__ == "__main__":
    script = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--script=")), "lao")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    r = derive(set(args) or None, force="--force" in sys.argv, script=script)
    print(json.dumps({"derived": r["derived"], "stencilled_glyphs": len(r["cuts"]),
                      "skipped_locked": r["skipped_locked"]}, ensure_ascii=False))
