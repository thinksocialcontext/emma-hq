# Connect your Shopify store

The shopify agent reads the store to keep `data/shopify.json` (the dashboard's Store sales panel) fresh and to check products. It reads first and changes nothing without your yes.

Two ways, pick one:

* **The Shopify connector in Claude Code (easiest).** Open Claude, look for Shopify in the connector list, and sign in to your store when asked. Nothing goes in `.env`.
* **A custom app with a read only token.** In Shopify admin open **Settings**, then **Apps and sales channels**, then **Develop apps**, and click **Create an app** (allow custom app development if Shopify asks). Name it `Emma HQ reader`. Under **Configure Admin API scopes**, tick only **read** scopes: `read_orders`, `read_products`, `read_inventory`, `read_customers` if you want customer counts. Save, click **Install app**, then reveal the **Admin API access token** once and copy it. Put it in `.env`:

```
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_ADMIN_TOKEN=paste-the-token-here
```

Then tell HQ: "Refresh the store numbers." Never paste the token into a chat. If you ever do, uninstall the app and make a new one.
