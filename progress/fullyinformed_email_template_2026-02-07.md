Subject: FullyInformed.com — sitemap URL inventory (posts)

Attached: `fullyinformed_posts_urls_only.csv`

What it contains
- ~36k post URLs discovered from the official WordPress sitemap index:
  - https://www.fullyinformed.com/wp-sitemap.xml

Next step (optional enrichment)
- If you want “title + short description next to each URL”, we can run an enrichment pass that fetches each URL and extracts:
  - HTML <title> / og:title
  - meta description / og:description (fallback to first content paragraph)

Note on runtime
- Enrichment over 36k URLs is a long run (hours to ~1 day depending on delay).
- We can run it in batches (e.g., 2k URLs per chunk) to keep it manageable.
