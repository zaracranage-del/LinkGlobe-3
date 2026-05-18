// /api/brand.js — Non-Amazon brand redirect (geo-aware where possible)
// Query params: us, uk, au, ca, de, handle
// Falls back to us if country-specific URL not supplied

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store, no-cache');

  const { us, uk, au, ca, de, handle } = req.query;

  if (!us) {
    return res.status(400).send('Missing us param');
  }

  const country = (req.headers['x-vercel-ip-country'] || 'US').toUpperCase();

  const urlMap = { GB: uk, AU: au, CA: ca, DE: de };
  const redirectUrl = urlMap[country] || us;

  // Log click to Supabase asynchronously (fire and forget)
  if (handle) {
    try {
      const SUPABASE_URL = process.env.SUPABASE_URL;
      const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY;
      if (SUPABASE_URL && SUPABASE_KEY) {
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
            country,
            store: 'brand',
            referrer: req.headers['referer'] || '',
            clicked_at: new Date().toISOString(),
          }),
        }).catch(() => {});
      }
    } catch (e) {}
  }

  res.redirect(302, redirectUrl);
};
