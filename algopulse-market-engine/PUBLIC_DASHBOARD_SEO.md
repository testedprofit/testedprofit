# Public Dashboard SEO Checklist

The dashboard now has a real title, meta description, Open Graph text, Twitter text, and WebApplication JSON-LD.

Do not add a canonical URL until the production domain is chosen. A fake canonical is worse than no canonical.

## Before Public Launch

- [ ] Pick one production URL, for example `https://algopulse.example.com/`.
- [ ] Add a canonical tag to `src/algopulse/static/index.html`.
- [ ] Add `og:url` with the same production URL.
- [ ] Add a real `og:image` URL.
- [ ] Add a sitemap entry if the dashboard is part of a larger static site.
- [ ] Keep internal links on the same `https` non-www trailing-slash format.
- [ ] Add auth or a reverse proxy rule if the dashboard exposes operational data.

## Suggested Tags

```html
<link rel="canonical" href="https://YOUR-DOMAIN/">
<meta property="og:url" content="https://YOUR-DOMAIN/">
<meta property="og:image" content="https://YOUR-DOMAIN/assets/og-image.jpg">
```

## Current Page Focus

Primary keyword:

```text
Algorand arbitrage scanner
```

Description:

```text
Monitor Algorand DEX spreads with AlgoPulse, a Tinyman and Pact market scanner for routing, paper trades, and guarded arbitrage execution.
```

