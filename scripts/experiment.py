"""Quick look: octilinearize every Lao glyph of Noto Sans Lao Black at a few settings and render."""
import sys
from lib import *  # noqa
from fontTools.ttLib import TTFont

settings = [dict(eps=10, min_edge=6), dict(eps=16, min_edge=10), dict(eps=24, min_edge=14)]
outs = []
for i, s in enumerate(settings):
    tt = TTFont(BASE)
    glyf = tt["glyf"]
    fails = []
    for name in lao_glyph_names(tt):
        try:
            c = contours_from_tt(tt, name)
            if not c:
                continue
            glyf[name] = tt_glyph(stylize.octilinearize(c, **s))
        except Exception as e:
            fails.append(f"{name}: {e}")
    out = ROOT / f"build/experiment-{i}.ttf"
    out.parent.mkdir(exist_ok=True)
    tt.save(out)
    outs.append(str(out))
    print(s, "fails:", fails[:5])
text = sys.argv[1] if len(sys.argv) > 1 else "ສະບາຍດີ ພາສາລາວ ຫຼວງພະບາງ ກິ່ງ ເຂົ້າ ນ້ຳ"
offline.specimen([str(BASE)] + outs, text, size=84, width=1700,
                 labels=["Noto Sans Lao Black (base)"] + [str(s) for s in settings]).save("/tmp/kp-exp.png")
