---
description: Put an ad batch on one contact sheet and rate its creative diversity
argument-hint: "[batch folder, default: newest in ads/batches/]"
---

The question: is this batch ten different reasons to buy, or one ad wearing ten outfits?

Input: $ARGUMENTS (default: the newest folder in `ads/batches/`). Use every still in its `final/` and the copy in `copy.json`.

## 1. One image
```
magick montage <-label "<id>: <headline>" image ...> -tile 4x -geometry 400x500+10+10 -pointsize 16 -background white <batch>/sheet.jpg
```
(On older ImageMagick use `montage` instead of `magick montage`.) Look at the sheet yourself before rating.

## 2. Score each 1 to 5, one line why, naming the ads that cause the score
* **Message (F.O.C.U.S.):** how many letters the batch really covers. Compare with what is already spending in `data/ads.json`: does it fill a gap or pile on?
* **Persona:** gave up for years, tried every metal, parent, collector or teacher, gift buyer.
* **Layout:** how many distinct layouts. The same template twice counts once.
* **Visual:** backgrounds, colors, product versus people versus type. Would Meta see these as the same image?
* **Hook:** do the first lines start differently, or say the same thing in new words?
* **Offer and claim:** how many lean on the same offer or price.

Then: an **overall score** out of 10 with a one sentence verdict, **clusters** Meta would treat as the same ad, the **three most valuable gaps** (each a one line concept with its letter), and **keep, cut or merge**.

Plain, direct, specific. No dashes. Save to `<batch>/diversity.md`. Do not change, launch or pause anything.
