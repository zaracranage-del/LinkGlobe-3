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

  res.redirect(302, redirectUrl);
};
