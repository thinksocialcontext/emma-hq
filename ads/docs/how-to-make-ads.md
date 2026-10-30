# How to make Earrings by Emma ads

Claude, this file teaches you to make static Meta ads for Earrings by Emma the way the October 2026 sample batch was made: ten 4:5 stills, each a different format, built on this computer from her real product photos with ImageMagick. No image model, no credits, nothing invented. It is self contained. If all you have is this file, her product photos and ImageMagick, you can do the whole job. If you also have the Emma HQ repository, the helpers in `ads/tools/` do the drawing for you (see "Optional helpers" at the end).

Write every word the owner or a customer will read without hyphens or dashes. Rewrite around them with a period, a comma or "and". The one exception is "e-commerce". Bullets use `*`.

## The rules that never bend

* **Never generate, redraw, recolour, warp or retouch the product.** The earring in an ad is always her real photo, cropped, scaled, framed or rotated, nothing more. Every ground, paper, stamp, arrow and texture is drawn in code around it.
* **The logo is her logo file, unchanged.** Scale it, put it on a white pill on dark grounds. Never retype or redraw it.
* **Every claim is on her site, at the same strength.** No medical claims. Do not say "hypoallergenic", "cures" or "safe for everyone" unless you quote the exact page that says it.
* **Reviews are quoted word for word**, with the name exactly as her site shows it (first name and last initial, plus town if shown).
* **Regular prices only** in evergreen ads. A sale price appears only in an ad made and dated for that sale, and only while it is live.
* **Kids:** her FAQ says not for very young children or new piercings. Any kids ad carries a line like "Not for little ones or new piercings". Confirm rights with the owner before using any photo of a child.
* **You never publish, launch, pause or fund an ad.** You prepare, the owner approves and launches.

## Step 1. Research from her site and her reviews

Read, and save notes with a URL for every fact:

* earringsbyemma.com: the homepage, the plastic post earrings page, the sensitive ears page, How We Started, FAQ, refund policy, warranty, shipping.
* The product catalogue and regular prices. On a Shopify store, `https://earringsbyemma.com/products.json` lists every product, its images and prices.
* Her reviews (the review wall and product pages). Copy customer sentences verbatim with the name as shown. Look for the words customers repeat: years without earrings, tried titanium, ears burning, holes closing, my daughter, I'm a teacher, don't look cheap.
* Her design system: colours from the theme and logo, fonts on the site.

Facts the sample batch used, all from her site in October 2026 (check they are still true before reusing):

* Every post and hook is plastic (polycarbonate), so there is no metal touching the ear. Polycarbonate is "the same material used in safety goggles, motorcycle helmets".
* Refund on the cost of up to 2 worn pairs that caused irritation; do not return worn earrings, just email the names.
* 2 year warranty. Family owned in Oklahoma, most pairs assembled by hand. Latex free posts, hooks and backs.
* Studs come with two sets of backs. Flexible hooks should thread out if pulled; no backs needed.
* Buy 3, get 1 free. Free shipping at 5 pairs. Digital gift cards from $25, emailed, no expiration date.
* Founding story: gold worked for Emma but was expensive, and after she lost a gold pair swimming the family started making plastic post earrings.

## Step 2. Pick the angles with F.O.C.U.S.

Every ad answers one reason to buy. Tag each with one letter:

| Letter | Means | Her customers say |
|---|---|---|
| F Frustration | the pain now | Titanium, surgical steel, nail polish, all failed. Ears sore by lunch. |
| O Outcome | the life after | "For the first time in 30 years, I can wear pierced earrings again." |
| C Constraint | what stops them, removed | My daughter's ears. Buying a gift without knowing her taste. |
| U Unspoken cost | the hidden cost | Gold prices for everyday earrings. A drawer of pairs she cannot wear. |
| S Skepticism | will it work, is plastic cheap | "These don't look 'cheap' or childish even if the posts are plastic." |

For a ten ad sample batch, use all five letters twice. For the weekly batch, follow the testing focus the owner set (see `weekly-batch.md` if you have it): one focus per batch, 5 to 10 ads.

Pair every angle with a persona from her reviews: gave up on earrings for years, tried every metal, parent of a child with sensitive ears, teacher, collector, gift buyer, someone with a drawer of unwearable earrings, skeptic who thinks plastic looks cheap.

## Step 3. Pick ten different formats from different families

Meta judges creative by how it looks. Meta's own words: "creative similarity refers to when ad images are visually too alike, even if technically different assets", and "When creative is too similar, our system may not recognize it as different and could deliver it to the same sets of audiences. This overlap limits your reach" (Meta for Business, "Demystifying creative diversification", 16 Dec 2025, and the Creative differentiation page). Ten ads in one template count as roughly one ad. So:

* Never repeat a format in a batch, and never repeat a ground colour and layout together.
* Spread across families: paper and handwriting, proof and review, comparison and data, product hero, native phone UI, editorial, offer. Aim for at least 3 families in a batch of 10; 4 or more is better.
* Look at the last two batches and prefer formats not used recently.
* Mix what carries the ad: product shots, people wearing them, pure type.

The sample batch used 3 families: six paper formats, two proof formats and two comparison formats. Next batches should add families it did not touch: a phone notes app or text thread, a review card wall, a newspaper style headline, a product macro, a bundle ladder.

## Step 4. Write the spec before building anything

For each ad write down, in one file per batch (`spec.json` if you use the helpers):

* id, file name, layout, F.O.C.U.S. letter, persona, link (the exact page the ad sends to)
* the photo files it uses, and the public URL each came from
* every string that will appear on the image, exactly
* ad copy: headline, primary text, description
* why it should win, in one sentence, naming the reviews it rests on

Check every string now: no dashes, every claim on the site, every price regular, every quote verbatim.

## Step 5. Get the photos

Download her public product images from the Shopify CDN (the image URLs in `products.json` or on product pages) and her logo SVG from the site. Keep a list: file, what it is, public URL, date. Prefer product shots on white for cards and lifestyle shots of the earring being worn for big prints. Never edit the photo itself.

The sample batch used these files (all on cdn.shopify.com under `/s/files/1/2480/4040/`): clear plastic post blanks, faux pearl studs lifestyle photo and 12mm product shot, petite faux diamond 6mm, soccer ball studs (worn, and product shot), gold rimmed glitter silver, diamond cut rhinestone, glassy butterfly, gummy bear purple, large clear hook blanks, moon cats, bendy pencil (worn, and product shot), infinity loops. The full list with URLs is `ads/assets/source-urls.tsv` in the repository.

## Step 6. Build the stills with ImageMagick

Output: 1080x1350 PNG (4:5). Videos, if ever, are 9:16. Keep the logo small, in a corner. Keep important text away from the bottom 120 px on feed placements.

### ImageMagick 6 and 7

* ImageMagick 7 has one command, `magick`. ImageMagick 6 (what `sudo apt install imagemagick` gives on Ubuntu and WSL) has `convert`, `identify`, `montage`, `composite` and no `magick`. Check with `command -v magick || convert -version`.
* The same options work in both. Write `magick in.png ... out.png` on 7 and `convert in.png ... out.png` on 6; `magick identify` becomes `identify`, `magick montage` becomes `montage`.
* Things that matter on 6: use `PNG32:out.png` to keep transparency; avoid `-type TrueColorAlpha`; use `-alpha extract`, `-alpha off` and `-compose CopyOpacity` for masks (all fine on 6.9); add `-seed N` before `+noise` so textures come out the same every time.
* SVG logos need librsvg. If `convert logo.svg logo.png` fails, run `sudo apt install librsvg2-bin` and use `rsvg-convert -w 1000 logo.svg -o logo.png`, then work from the PNG.

### Fonts

* Fjalla One for headings, Poppins (Regular, Medium, SemiBold, Bold, ExtraBold) for body: the fonts on her site.
* Permanent Marker for handwriting and chalk.
* Liberation Mono (`sudo apt install fonts-liberation`) or Cousine for receipts and labels.
* All are free from github.com/google/fonts (`ofl/fjallaone`, `ofl/poppins`, `apache/permanentmarker`, `ofl/cousine`). If one is missing, use the nearest you have and say so; never let a random default font into a finished ad.

### Colours

Pink `#FD0082`, teal `#2FBAD1`, purple `#5E106B`, lavender `#8B85C1`, cream `#FEFCE8`, ink `#231A2B`. White type on pink, purple or teal grounds; purple or ink type on light grounds.

### The building blocks

Every layout below is made from a handful of moves. On ImageMagick 6 replace `magick` with `convert`.

* Paper ground with grain: `magick -size 1080x1350 xc:'#EDEAF7' \( -size 1080x1350 xc:gray50 -seed 1 -attenuate 1 +noise Gaussian -modulate 100,0 -blur 0x0.7 +level 47%,53% \) -compose overlay -composite PNG32:ground.png`
* Text that fits a width: `magick -background none -fill '#5E106B' -font FjallaOne-Regular.ttf -pointsize 96 -interline-spacing -10 -size 960x caption:'Tried everything?\nTry no metal.' -trim +repage PNG32:title.png` (use `label:` instead of `-size ... caption:` for one line at natural width)
* Fill crop a photo: `magick photo.jpg[0] -resize 320x320^ -gravity center -extent 320x320 +repage PNG32:crop.png`
* White print border: `magick crop.png -bordercolor white -border 16 PNG32:card.png`; caption strip under it: `-gravity South -background white -splice 0x70`
* Round window: draw a white circle on `xc:none` of the same size, then `magick crop.png mask.png -compose CopyOpacity -composite PNG32:round.png`
* Tilt: `magick card.png -background none -rotate 5 PNG32:tilt.png`
* Drop shadow: `magick tilt.png \( +clone -background black -shadow 40x12+0+10 \) +swap -background none -layers merge +repage PNG32:shadowed.png`
* Place: `magick ground.png shadowed.png -gravity NorthEast -geometry +22+640 -composite PNG32:ground.png`
* Masking tape: `magick -size 150x44 xc:'#F6EFC8C8' PNG32:tape.png`, placed over the top edge of a print
* Strike through a word: draw `-stroke '#FD0082B0' -strokewidth 4 -draw "stroke-linecap round line x1,y1 x2,y2"` across its middle
* Marker arrow: `-fill none -stroke '#5E106B' -strokewidth 7 -draw "stroke-linecap round path 'M 150,500 Q 230,560 330,520'"` plus two short lines for the head
* Worn stamp or chalk: extract the alpha (`-alpha extract`), multiply it by sparse noise (`-fill white -colorize 100 -seed 1 -attenuate 0.6 +noise Impulse -threshold 35%`), copy it back with `-compose CopyOpacity`
* Logo on a pill: render the SVG at `-density 400`, trim, resize to 200 to 230 px wide, composite it centred on a white `roundrectangle` 44 px wider and 30 px taller

### The ten layouts

Coordinates are on the 1080x1350 canvas, from the top left unless a corner is named. The type sizes are ImageMagick point sizes. Photo counts are in brackets.

**1. Notepad list, crossed out** (format pp02, family paper). For F or S. Fields: title, kicker, crossed (up to 6 lines), final, photo caption, footer. [1 product shot]
* Ground lavender paper `#EDEAF7` with small dots `#D9D4EE` on a 60 px staggered grid.
* Title Fjalla One 96 purple at 60,50.
* A white notepad 600x760: pale teal lines every 74 px from y 190, a pink margin line at x 78, a purple binding strip 46 px tall with round holes. Kicker in Permanent Marker 36 purple at 100,98. Each failed fix in Permanent Marker 40 ink, struck through in translucent pink. The final line in teal, circled with a teal ellipse. Notepad rotated minus 2.5 degrees, shadow, placed at 36,300.
* Product shot 320x320 with a white border, a caption strip in Permanent Marker 34, tape on top, rotated 5 degrees, at the right edge around y 640.
* Footer Poppins SemiBold 32 purple at 60,1254. Logo pill 220 wide bottom right.
* Sample: "Things I tried for my ears": Titanium, Surgical steel, Nickel free posts, Clear nail polish trick, 14k gold, then "No metal in the ear". Title "Tried everything?\nTry no metal."

**2. Giant quote poster** (pr02, proof). For O or S. Fields: big (first half of the quote), big2 (the punch), attribution, photo caption, footer. [1 lifestyle photo of the earring worn]
* Pink paper ground. A huge translucent white opening quote mark (Fjalla One 300) top left.
* First half in Fjalla One 70 white, the punch line in Fjalla One 128 white, both 960 wide from 60,140. A short teal rule under them, then the attribution in Poppins Medium 28 white, 520 wide.
* Photo 430x500 cropped from the right, rounded corners, on a white rounded frame with a caption strip, rotated 3 degrees, bottom right with a shadow.
* Footer Poppins Bold 34 white bottom left, logo pill above it.
* Sample: "For the first time in 30 years," / "I can wear pierced earrings again." / "Karen D., verified review of the Faux Pearl Studs, earringsbyemma.com".

**3. Stamped certificate** (pr03, proof). For S. Fields: kicker, title, body (the policy, quoted exactly), stamp (two lines), seal (two lines), sign, footer. [1 product shot]
* Lavender ground. A cream certificate 960x1150 centred near the top with a thick purple border and a thin inner border, pink dots in the corners.
* Kicker in Poppins Bold 26 teal, wide letter spacing, centred. Title Fjalla One 112 purple, centred. A short pink rule. Body Poppins Medium 34 ink, 760 wide, centred. A signature line in Permanent Marker 40 with a rule under it.
* Product in a round window 300 px with a purple ring, bottom right of the certificate. Footer and the logo bottom left.
* A pink rubber stamp (two circles, two lines of text, worn edges, 66% size, rotated minus 14) around 350,822 and a teal rosette seal 190 px (48 point star, text in white) around 120,836.
* Sample: "THE SENSITIVE EARS PROMISE", "Try two pairs.\nRisk free.", stamp "2 PAIRS / RISK FREE", seal "2 YEAR / WARRANTY", "From our refund policy".

**4. School notebook with taped photo** (pp08, paper). For C, parents, back to school. Fields: title, lines (up to 3), quote, quote by, note (the safety line), photo caption, footer. [1 photo worn, 1 product shot]
* Ground: black and white composition notebook marble (random noise, blur, threshold, morphology open, two colours).
* A cream lined page 980x1200 at 50,40: pale teal lines every 62 px from y 330, pink margin at x 96.
* Title Fjalla One 82 purple at 126,70. Each line gets a hand drawn teal tick and Permanent Marker 34 text, 124 px apart.
* A pink sticky note `#FFC3E2` 420x315 with the quote in Poppins SemiBold 28 and the name below, rotated minus 3, at 110,660 on the page.
* Note in Poppins SemiBold 30, footer Poppins Bold 34 purple, logo under it.
* A taped print of the earring being worn, 330x380, rotated 4, right side around y 690, and a small product card 150 px tilted minus 6 above it.
* Sample lines: "Plastic posts, no metal touching the ear", "Two sets of backs in every stud pair", "Flexible hooks should thread out if pulled". Note: "Not for little ones or new piercings".

**5. Store receipt** (pp03, paper). For U or C. Fields: title, receipt head (two lines), rows (label and value, up to 8; a blank row is a dotted divider; rows before it are struck through, rows after it are bold with pink values), foot, footer. [1 product shot]
* Teal ground. Title Fjalla One 100 white at 60,50.
* A receipt 600x760 with a zigzag torn bottom: header in Liberation Mono Bold 34, subhead mono 22 grey, dotted dividers, rows in mono 26 with values right aligned, a centred foot line, a drawn barcode. Rotated 2 degrees, right side from y 300.
* Product in a round plate 330 px, bottom left with a shadow. Footer Poppins SemiBold 26 white, logo pill.
* Sample rows: "14K GOLD STUDS / $50 TO $200+", "LOST A PAIR SWIMMING / REPLACE IT?", divider, "FAUX PEARL STUDS / $16", "PLASTIC POSTS / NO METAL", "BUY 3 / GET 1 FREE". Footer "Gold price range quoted from earringsbyemma.com".

**6. Display card board** (cd04, comparison). For O, collectors, a live bundle offer. Fields: title, cards (exactly 6, name and price), offer, offer2, footer. [6 product shots]
* Purple ground with pegboard holes `#4A0C55` every 48 px. Title Fjalla One 104 white, centred at the top.
* Six white display cards 300x430 in two rows of three (top left corners near 60,200; 390,210; 720,200; 60,650; 390,660; 720,650), each with a hanger slot, the product cropped 260x250, the name in Poppins SemiBold 24 centred, the price in Fjalla One 34 pink, each tilted between minus 2 and 2 degrees.
* A pink rounded offer pill bottom left (offer in Fjalla One 60, offer2 in Poppins SemiBold 30), footer bottom right, logo pill.
* Sample: Petite Faux Diamond $25, Faux Pearl $16, Gold Rimmed Glitter $15, Diamond Cut $15, Glassy Butterfly $14, Gummy Bear $14. "Buy 3, get 1 free" / "Free shipping at 5 pairs".

**7. Annotated photo with marker arrows** (pp11, paper). For U, C or S. Fields: title, sub, notes (up to 3: two arrow notes and a price sticker), quote, quote by, footer. [1 product shot]
* Light pink ground `#FFE6F3`. Title Fjalla One 80 purple at 60,46, sub Fjalla One 80 pink under it.
* The product as a large white bordered print 600x600, rotated minus 2, at 230,320.
* Note 1 in Permanent Marker 42 purple at 40,380 with a curved arrow to the product; note 2 at 40,990 with a long arrow up into the photo; note 3 on a pink circle sticker 210 px, rotated 10, top right of the photo.
* A white quote card with a teal bar on its left, bottom right. Footer Poppins Bold 27 purple at 60,1180, logo pill under it.
* Sample: "That drawer of earrings\nyou stopped wearing?" / "Swap the hooks." Notes "clear plastic,\nno metal", "the curve holds it,\nno backs needed", "5 pairs for $5".

**8. Kraft gift tag** (pp05, paper). For C (gift buyers) or seasonal O. Fields: kicker, title, sub, footer. [2 product shots]
* Kraft paper ground `#C49A6C` with heavy grain and fine fibre lines; a pink ribbon band across the top.
* Two white bordered product prints tucked behind the tag on the right (330 px rotated 8, 250 px rotated minus 7).
* A cream tag 640x900 with clipped top corners, a lavender inner line and a punched hole, rotated minus 4, at 40,200, with a string drawn up from the hole. Kicker Poppins SemiBold 34 purple, title Fjalla One 140 pink, a lavender rule, sub Poppins Medium 32 ink, logo at the bottom of the tag.
* A purple band along the bottom 120 px with the footer in white.
* Sample: "Shopping for sensitive ears?" / "Let them pick." / "Digital gift cards from $25,\nemailed, no expiration date".

**9. Chalkboard** (pp09, paper). For F, teachers and school themes. Fields: title, sub, quote, quote by, photo caption, footer. [1 photo worn, 1 product shot]
* A wooden frame (brown paper grain with motion blur), a slate board `#26332D` 1020x1200 at 30,30 with faint chalk smudges, a chalk tray line near the bottom.
* All board text gets worn chalk edges: title Fjalla One 150 near white at 80,80 with a pink chalk underline; sub Permanent Marker 50 pale blue; quote Permanent Marker 40 pale pink, 480 wide; name Poppins 24 grey.
* A pinned photo print 400x440 (white border, caption strip, pink pin), rotated 5, right side around y 600. A small product card 220 px tilted minus 6 bottom left.
* Footer Poppins SemiBold 30 white on the frame, logo pill bottom right.
* Sample: "Ears sore\nby lunch?" / "Plastic hooks.\nNo metal in the ear." / "\"I'm a teacher, and these are my fave!\"" Shelly H., Bendy Pencil Dangles.

**10. Material spec sheet** (cd03, comparison). For S about quality or materials. Fields: kicker, title, rows (up to 6, label and value), figure caption, quote, quote by, footer. [1 product shot]
* White ground with a faint teal 40 px grid; white panels behind the header (40,30 to 1040,320) and the table (40,800 to 1040,1320).
* Kicker Liberation Mono Bold 26 teal, spaced, at 60,60, a purple rule at y 104, title Fjalla One 96 purple at 60,122.
* Product 430x430 with a thin purple frame at 60,340, a figure caption in mono 23 under it at y 788.
* A pink rounded quote panel 530,340 to 1020,776 with a big pink quote mark, the quote in Poppins SemiBold 34 and the name in Poppins Medium 24.
* The table from y 830: 56 px rows, alternate rows tinted `#EAF8FB`, labels mono bold 22 purple at x 80, values Poppins Medium 28 ink at x 380, a purple rule under. Footer Poppins Bold 32 pink, logo bottom right.
* Sample rows: POST AND HOOK / Polycarbonate, no metal; ALSO USED IN / Safety goggles, helmets; LATEX FREE / Posts, hooks and backs; HOOKS / Flexible, no backs needed; WARRANTY / 2 years; ASSEMBLED / Most pairs by hand, Oklahoma. Figure "FIG. 1  Infinity Loops, plastic hooks".

### Write a record beside every still

For each PNG write `<file>.md`:

* the line "Edited, not generated. No image model touched this still and no credits were spent."
* layout, persona, F.O.C.U.S. letter, link
* a sources table: path, what it is, what was done (for example "cropped square, white border, tilted"), public URL; the logo too
* every string that renders, one per bullet
* the ad copy: headline, primary text, description, and why it should win

## Step 7. The critic pass

Before the owner sees anything, check every still as if someone else made it. If you can, use a fresh session or a separate agent. Write `critic.md` with PASS or FAIL per ad and the reason.

1. **Right product.** The earring in the photo is the product named in the copy and the link.
2. **Text.** Spelled right, readable at phone size, nothing cut off or overlapping, no dashes.
3. **Logo.** Her file, not stretched, not recoloured.
4. **Claims.** Every claim is on her site at the same strength. No medical promises. Offers are live today. Prices are regular prices.
5. **Reviews.** Every quote exists on her site, word for word, with the name as shown.
6. **Variety.** No two ads share a format, or a layout and ground colour.

Fix and check again until every ad passes. The sample batch took three rounds. The critic's main catch was claims that went further than her site. "No metal at all" went further than the site, whose claim is about the post and hook, the part that touches the ear. It became "no metal in the ear" and "no metal touching the ear". Treat any absolute ("never", "all", "100%", "safe for everyone") as suspect until you find it on her site.

## Step 8. Contact sheet and the diversity rating

Put the batch on one image:

```
magick montage -label '%t' final/*.png -tile 4x -geometry 400x500+10+10 -background white sheet.jpg
```

(ImageMagick 6: `montage` instead of `magick montage`.) Look at it yourself. Then rate it (the `/rate` command in Emma HQ does this): score message, persona, layout, visual, hook and offer from 1 to 5, give an overall score out of 10, name any clusters Meta would see as the same ad, and the three most valuable gaps. Cut or replace any ad that clusters with another.

## Step 9. Ask the owner, then stop

Write `approvals/<date>-ad-batch.md` with the sheet path, the critic result, the diversity score, the ads table (file, layout, letter, headline) and the budget being asked for. Then stop. The owner approves and launches, or tells you exactly which ads to launch. Name ads `<letter> | <short name>` and the ad set after its launch date so results can be tracked.

## Optional helpers in the Emma HQ repository

If you have the repository, you do not need to type the commands above:

* `python3 ads/tools/fetch_sources.py` downloads every image in `ads/assets/source-urls.tsv` into `ads/assets/photos/` and the logo into `ads/assets/logo/`, and writes `sources.csv` with the public URLs.
* `python3 ads/tools/build_stills.py ads/batches/<date>` builds every ad in `<date>/spec.json`, writes the Markdown records and `sheet.jpg`. Add `--check` to validate only. It refuses dashes on the image or in the copy, missing photos and unknown layouts. `--layouts` lists the ten layouts and their fields.
* The ten layouts are in `ads/tools/layouts/` (`notepad`, `quote_poster`, `certificate`, `notebook`, `receipt`, `display_board`, `annotated`, `gift_tag`, `chalkboard`, `spec_sheet`), one file each. The four older simple layouts (`poster`, `review`, `note`, `tried`) still work.
* `ads/tools/imkit.py` detects ImageMagick 6 or 7 and uses the right commands. `EMMA_IM=6` forces the ImageMagick 6 commands.
* `ads/batches/examples/2026-10-29/spec.json` is the sample batch written out in full: every string, photo and colour of all ten ads. Copy it to start a new batch, then change the angles, strings and photos.
* `./setup.sh` installs ImageMagick and fetches the fonts.

To add a new format, copy the closest layout file, give it a new `NAME`, and keep the same rules: real photos, drawn grounds, every string from the spec.
