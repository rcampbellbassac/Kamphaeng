"""Proof sheets for the current build -> /tmp/kp-*.png"""
import sys
from lib import *  # noqa
F = str(ROOT / "fonts/Kamphaeng-Regular.ttf")
BO = str(LATIN)
offline.render_text(F, "ສະບາຍດີ ພາສາລາວ\nຫຼວງພະບາງ BLACK OPS\nນ້ຳຕົກຕາດກວາງຊີ 2026", size=120, guides=False).save("/tmp/kp-hero.png")
offline.specimen([F, BO], "LAO STENCIL ລາວ 0123", size=90, width=1500, labels=["Kamphaeng (draft)", "Black Ops One"]).save("/tmp/kp-vs.png")
offline.render_text(F, offline.SAMPLES["stacking"], size=72, guides=True).save("/tmp/kp-stack.png")
offline.glyph_grid(F, cell=130, cols=13).save("/tmp/kp-grid.png")
print(offline.mark_collisions(F))
print(offline.font_info(F)["lao"]["core_present"], "/ 65 Lao core;", offline.font_info(F)["metrics"])
