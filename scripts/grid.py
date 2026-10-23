import sys
from lib import *  # noqa
f = sys.argv[1]
offline.glyph_grid(f, cell=130, cols=13).save("/tmp/kp-grid.png")
