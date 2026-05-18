// /api/index.js — Amazon geo-redirect
// Vercel automatically sets x-vercel-ip-country on every request

const STORES = {
  AU: 'https://www.amazon.com.au',
  GB: 'https://www.amazon.co.uk',
  DE: 'https://www.amazon.de',
  FR: 'https://www.amazon.fr',
  CA: 'https://www.amazon.ca',
  JP: 'https://www.amazon.co.jp',
  IN: 'https://www.amazon.in',
  IT: 'https://www.amazon.it',
  ES: 'https://www.amazon.es',
  NL: 'https://www.amazon.nl',
  SG: 'https://www.amazon.sg',
  MX: 'https://www.amazon.com.mx',
  US: 'https://www.amazon.com',
};

// Map country code → which tag param to use
const TAG_PARAM = {
  AU: 'au_tag',
  GB: 'uk_tag',
  US: 'us_tag',
  CA: 'ca_tag',
  DE: 'de_tag',
  JP: 'jp_tag',
  FR: 'fr_tag',
  IT: 'it_tag',
  ES: 'es_tag',
  NL: 'nl_tag',
  SG: 'sg_tag',
  MX: 'mx_tag',
  IN: 'in_tag',
};

module.exports = (req, res) => {
  // CORS for any potential direct fetch
  res.setHeader('Access-Control-Allow-Origin', '*');

  const { asin, tag, handle, ...rest } = req.query;

  if (!asin) {
    return res.status(400).send('Missing asin');
  }

  // Vercel sets this header automatically — no external API needed
  const country = (req.headers['x-vercel-ip-country'] || 'US').toUpperCase();

  // Pick the right store
  const store = STORES[country] || STORES['US'];

  // Pick the right affiliate tag for this country
  const tagParam = TAG_PARAM[country];
  const affiliateTag = (tagParam && rest[tagParam]) ? rest[tagParam] : (tag || 'notag');

  // Build redirect URL
  const redirectUrl = `${store}/dp/${asin}?tag=${affiliateTag}&linkCode=ogi&th=1&psc=1`;

  // Log click to Supabase asynchronously (fire and forget)
  if (handle) {
    try {
      const SUPABASE_URL = process.env.SUPABASE_URL;
      const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY;
      if (SUPABASE_URL && SUPABASE_KEY) {
        const referrer = req.headers['referer'] || '';
        fetch(`${SUPABASE_URL}/rest/v1/link_clicks`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`,
            'Prefer': 'return=minimal',
          },
          body: JSON.stringify({
            handle,
            asin,
            country,
            store: 'amazon',
            referrer,
            clicked_at: new Date().toISOString(),
          }),
        }).catch(() => {});
      }
    } catch (e) {}
  }

  // 302 redirect (not 301 — we want it re-evaluated each time for geo accuracy)
  res.setHeader('Cache-Control', 'no-store, no-cache');
  res.redirect(302, redirectUrl);
};
