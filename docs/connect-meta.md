# Connect your Meta ads numbers

The dashboard's ads pages (Weekly launch, Ads tracker, F.O.C.U.S.) read one file: `data/ads.json`. The ads agent fills it with `ads/tools/meta_pull.py`. Everything here is **read only**: nothing in Emma HQ can launch, pause, edit or fund an ad.

There are three ways to get the numbers in. Pick one.

| Route | Setup | Refresh | Best for |
| --- | --- | --- | --- |
| A. Ads Manager CSV export | none | you export a file each week | trying Emma HQ today |
| B. A Meta app with a read only token | about 20 minutes, once | automatic, the ads agent does it | the weekly rhythm (recommended) |
| C. A Meta Ads connector in Claude Code | depends on the connector | the agent asks the connector | if you already use one |

**Our recommendation:** start with **A** this week so the dashboard shows your real ads straight away. Then set up **B** once. After that the ads agent refreshes the numbers by itself before every weekly batch and every `/status`, and you never export again.

**One rule for every route:** your token is a password. It goes in the `.env` file and nowhere else. Never paste it into a chat with an agent, an email, a brief or a memory. If you ever do, make a new token (step B5) and the old one stops working.

## Name your ads so the dashboard can sort them

The tracker sorts every ad into a F.O.C.U.S. bucket and a weekly batch from its name:

* Start the **ad name** with its letter and a bar: `S | Tried every metal, poster`. (`[S] Tried every metal` works too.)
* Name the **ad set** after the batch's launch date: `2026-11-04`.

The ads agent writes ad names this way in every batch. For ads made before Emma HQ, ask the ads agent to make `data/ad-tags.json`, which sets the letter and batch by ad id without renaming anything in Meta.

## A. Ads Manager CSV export (zero setup)

1. Open **Ads Manager** (adsmanager.facebook.com) and choose your ad account.
2. Click the **Ads** tab (not Campaigns or Ad sets).
3. Set the date range to **Last 30 days**.
4. Click **Columns**, then **Customize columns**, and make sure these are ticked: Ad name, Ad set name, Delivery, Amount spent, Purchases, Purchases conversion value, CTR (link click through rate), Starts. Click **Apply**.
5. Click **Reports** (or **Export**), then **Export table data**, choose **.csv**, and export.
6. Move the file into a folder called `exports` inside your Emma HQ folder (make the folder the first time; git ignores it) and tell HQ: "Load the Meta export in exports/." Or run it yourself:

```
python3 ads/tools/meta_pull.py --csv exports/your-export.csv
```

It prints how many ads spent and the total, then writes `data/ads.json`. Refresh the dashboard.

A CSV has no 7 day totals, so the Overview shows 30 day numbers until you switch to route B. Repeat the export before each weekly batch.

## B. A Meta app with a read only System User token (recommended)

You need admin access to the business portfolio that owns the ad account. Meta renames menus from time to time; if a label below differs a little, pick the closest match.

### B1. Create the app

1. Go to **developers.facebook.com**, log in with your Facebook account, and click **My Apps**, then **Create App**.
2. When asked what the app should do, choose the option for **Other**, then choose the app type **Business**.
3. Name it `Emma HQ reader`, enter your email, and pick your **business portfolio** (Earrings by Emma). Click **Create app**.
4. On the app's dashboard, find **Marketing API** in the list of products and click **Set up**. You do not need to submit anything for review: reading your own ad account works without it.

### B2. Make a System User

1. Go to **business.facebook.com/settings** (Business settings).
2. In the left menu open **Users**, then **System users**, and click **Add**.
3. Name it `emma-hq-reader` and give it the **Employee** role (not Admin). Click **Create system user**.

### B3. Give it view only access to the ad account

1. With the system user selected, click **Assign assets** (or **Add assets**).
2. Choose **Ad accounts**, tick your ad account, and turn on **only** the permission to **view performance** (it may be called View performance or Analyze). Leave every "manage" permission off.
3. Click **Save changes**.

### B4. Connect the app to the system user

1. Still in Business settings, open **Accounts**, then **Apps**, and check that `Emma HQ reader` is listed. If not, click **Add** and connect it by its App ID (shown at the top of the app dashboard in developers.facebook.com).
2. Back in **System users**, select `emma-hq-reader`, click **Assign assets**, choose **Apps**, tick `Emma HQ reader`, and give it **Develop app** access if asked.

### B5. Make the token

1. Select `emma-hq-reader` and click **Generate new token**.
2. Choose the app `Emma HQ reader`.
3. For expiry, choose **Never** if offered (otherwise you repeat this when it expires).
4. Tick **one** permission only: **ads_read**. Do not tick ads_management or anything else.
5. Click **Generate token** and copy it. Meta shows it once.

### B6. Put it in .env

Find your ad account number: in Ads Manager it is in the account menu at the top, or in the web address after `act=`. Digits only.

Open `.env` in your Emma HQ folder (for example `nano .env` in Ubuntu, or open the folder in Windows File Explorer through `\\wsl$\Ubuntu\home\<you>\emma-hq`) and fill in these two lines:

```
META_ACCESS_TOKEN=paste-the-token-here
META_AD_ACCOUNT_ID=1234567890
```

Save the file. `.env` is ignored by git, so it never leaves your computer.

### B7. Test it

```
python3 ads/tools/meta_pull.py --check
```

You should see `Connected to ad account "..." (USD, active). The token works and was not printed.` If you see an error, it names what is wrong (a missing line in `.env`, or what Meta said) without showing the token. Then pull the numbers:

```
python3 ads/tools/meta_pull.py
```

From now on the ads agent runs this itself before every weekly batch and every `/status`.

## C. A Meta Ads connector in Claude Code

Some people connect Meta to Claude through a connector (an MCP server) instead of a token. If you prefer that, open Claude, **check the connector list in Claude** for a Meta Ads connector, and follow its own sign in steps. We do not name a specific one here because the choices change; ask ThinkSocial before installing one you are unsure of.

Two rules if you go this way:

* Give it **read only** access. If the connector asks for permission to manage, create or pause ads, say no or choose a read only option.
* The ads agent still writes `data/ads.json` in the same shape (see `docs/dashboard.md`), so the dashboard works the same. Tell HQ: "Use the Meta connector to refresh data/ads.json, read only."

## Troubleshooting

* **"META_ACCESS_TOKEN missing from .env"**: the line is blank or misspelled. Check there are no spaces around `=`.
* **"Meta said ... (error 190)"**: the token expired or was revoked. Make a new one (B5).
* **"(error 200)" or another permissions error**: the system user cannot see the ad account. Repeat B3.
* **Ads show no bucket letter**: rename them as above, or ask the ads agent for `data/ad-tags.json`.
* **Numbers look different from Ads Manager**: the tool counts purchases once (it takes Meta's combined purchase count and does not add pixel and app purchases twice) over the last 30 days. Check the date range and attribution setting in Ads Manager.
