# Product and collection hygiene

A monthly read only sweep. Report findings in `shopify/hygiene-<date>.md`, grouped by how much they matter, each with a proposed fix.

* **Titles** follow the house pattern: "<Name> <Studs|Dangles> Plastic Post Earrings for Sensitive Ears".
* **Descriptions** use the site's approved claims only (memory `no-medical-claims`), mention materials and care, and have no dashes in new copy.
* **Images** have alt text that describes the earring. Size shots exist for bestsellers.
* **Tags and collections:** every product sits in at least one browse collection (Studs or Dangles, a theme, Kids if suitable). Seasonal collections are switched before the season.
* **The public product feed** (`/products.json`) can be read by anyone. Check what vendor names and internal tags it exposes and propose cleaning anything the owner would not want public.
* **Theme:** note duplicate or preview themes that are live by accident.
* **Reviews counts** quoted on pages match the current Loox total.
* **Offers** on banners, cart and product pages match each other and the policy pages.
