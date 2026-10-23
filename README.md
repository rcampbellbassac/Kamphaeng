# Kamphaeng (ກຳແພງ) — working name

A heavy Lao + Latin stencil display font in the spirit of Black Ops One. SIL Open Font License 1.1.

- **Lao**: outlines derived from Noto Sans Lao (Black instance), rebuilt from straight edges at
  0/45/90 degrees (curves become chamfers, bowls become octagons) with stencil gaps: every enclosed
  counter is opened, plus up to two junction gaps per letter. Noto's Lao OpenType layout (narrow/small
  mark alternates, mark/mkmk positioning) is kept, so stacked vowels and tones work.
- **Latin, digits, punctuation**: Black Ops One, scaled to 1000 UPM.

## Files

| Path | What |
|---|---|
| `sources/Kamphaeng-Regular.ufo` | Lao design source; open and edit in FontLab (fontlab-mcp) |
| `design/overrides.json` | per-glyph design decisions (extra cuts, disable auto gaps, tolerance) |
| `scripts/derive.py` | (re)generate unlocked Lao glyphs in the UFO from Noto Sans Lao Black |
| `scripts/build.py` | build `fonts/Kamphaeng-Regular.ttf` + `.woff2` |
| `scripts/proof.py` | proof sheets |

Glyphs hand-edited in FontLab go in the UFO lib list `kamphaeng.locked` so `derive.py` never overwrites them.
Tooling: `~/Source/fontlab-mcp` (`fontlab_mcp.stylize`).
