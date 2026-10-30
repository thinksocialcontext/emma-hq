# Zero credit ad stills

Make every still from real product photos, the logo, fonts and shapes drawn in code. No image model, no credits, nothing that can invent a fake earring.

## Sources

* Product photos from Shopify (cutouts on white work best). Save each to `batches/<date>/photos/` and note where it came from.
* Real customer or team photos only with the owner's OK, and only people the owner confirms.
* Brand fonts in `assets/fonts/` (Fjalla One and Poppins are free Google Fonts; `./setup.sh` can fetch them).

## Build

```
python3 ads/tools/build_stills.py ads/batches/2026-11-04
```

Layouts today: `poster` (big type over a cutout), `review` (a real review card), `note` (sticky note on a full bleed photo), `tried` (crossed out list of what failed, then what worked). Add more layouts to the script as the account learns: receipt, text thread, price tag, ruler size shot, before and after jewelry box, calendar of holidays.

The builder writes a Markdown record beside every still: "Edited, not generated", the sources, and every string on the image. It refuses copy with a dash.

## Rules

* The earring is never redrawn, recolored, warped or retouched.
* No two ads in a batch share a layout and background.
* Logo small and in a corner.
* Every claim true and sourced. See memory `no-medical-claims`.

If a scene truly cannot be photographed or built, list the image, the tool and its cost, and ask the owner first.
