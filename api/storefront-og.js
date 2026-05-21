// /api/storefront-og.js — zero npm dependencies, native fetch only
module.exports = async (req, res) => {
  const handle = (req.query.handle || '').toLowerCase().trim();
  if (!handle) return res.status(400).send('Missing handle');

  const SB_URL = process.env.SUPABASE_URL;
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

  let profile = null;
  try {
    const r = await fetch(
      `${SB_URL}/rest/v1/signups?handle=eq.${encodeURIComponent(handle)}&select=name,bio,avatar_url,handle&limit=1`,
      { headers: { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}` } }
    );
    const rows = await r.json();
    profile = rows?.[0] || null;
  } catch (e) {
    console.error('storefront-og fetch:', e.message);
  }

  if (!profile) return res.status(404).send('Not found');

  const name  = profile.name || handle;
  const bio   = profile.bio  || `Shop ${name}'s curated picks — geo-smart links that work worldwide.`;
  const url   = `https://linkglobe.co/${handle}`;
  const image = profile.avatar_url || 'https://linkglobe.co/og-image.png';
  const title = `${name} on LinkGlobe`;

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 's-maxage=3600');
  res.send(`<!DOCTYPE html><html><head>
  <meta charset="UTF-8">
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(bio)}">
  <meta property="og:title" content="${esc(title)}">
  <meta property="og:description" content="${esc(bio)}">
  <meta property="og:url" content="${esc(url)}">
  <meta property="og:image" content="${esc(image)}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${esc(title)}">
  <meta name="twitter:description" content="${esc(bio)}">
  <meta name="twitter:image" content="${esc(image)}">
  <meta http-equiv="refresh" content="0;url=${esc(url)}">
</head><body><p>Redirecting to <a href="${esc(url)}">${esc(url)}</a>…</p></body></html>`);
};

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
