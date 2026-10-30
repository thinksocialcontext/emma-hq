"""The layout catalogue. One module per layout; each exposes the same attributes:

  NAME       the value of "layout" in spec.json
  FORMAT     the format library id it implements (family letters plus number)
  FAMILY     the format family, used to spread a batch across families
  TITLE      a short human name
  WHEN       when to use it
  PHOTOS     one description per photo slot, in order ("what was done", for the record)
  REQUIRED   on_image fields that must be present: {"field": "str" | "list" | "pair" | "rows" | "cards"}
  OPTIONAL   on_image fields that may be present, same shape
  LIMITS     {"field": max_items} for list fields
  COLORS     the default colours the layout reads (merged over the brand palette; spec may override)
  build(k, t) draws the ad with Kit k from on_image dict t and returns the canvas path

ads/docs/how-the-sample-ads-were-made.md lists them with a picture of each.
"""

from importlib import import_module

MODULES = ["notepad", "quote_poster", "certificate", "notebook", "receipt",
           "display_board", "annotated", "gift_tag", "chalkboard", "spec_sheet"]

LAYOUTS = {}
for _name in MODULES:
    _mod = import_module(f"{__name__}.{_name}")
    LAYOUTS[_mod.NAME] = _mod

# The four simple layouts from the first kit (single photo, flat fields) live in classic.py.
from . import classic  # noqa: E402

CLASSIC = classic.LAYOUTS
