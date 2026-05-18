// /api/storefront-og.js
// Returns a minimal HTML page with proper OG/meta tags for a creator's storefront.
// Used by social crawlers (Facebook, Twitter, iMessage etc.) which don't run JS.
// Vercel routes /:handle to storefront.html for browsers, but this endpoint
// can be called as /api/storefront-og?handle=xyz for OG preview generation.

const { createClient } = require('@supabase/supabase-js');

module.exports = async (req, res) => {
  const handle = (req.query.handle || '').toLowerCase().trim();
  if (!handle) return res.status(400).send('Missing handle');

  const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_KEY
  );

  const { data: profile } = await supabase
    .from('signups')
    .select('name, bio, avatar_url, handle')
    .eq('handle', handle)
    .single();

  if (!profile) {
    return res.status(404).send('Not found');
  }

  const name    = profile.name || handle;
  const bio     = profile.bio  || `Shop ${name}'s curated picks — geo-smart links that work worldwide.`;
  const url     = `https://linkglobe.co/${handle}`;
  const image   = profile.avatar_url || 'https://linkglobe.co/og-image.png';
  const title   = `${name} on LinkGlobe`;

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 's-maxage=3600');
  res.send(`<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(bio)}">
  <meta property="og:title"       content="${esc(title)}">
  <meta property="og:description" content="${esc(bio)}">
  <meta property="og:url"         content="${esc(url)}">
  <meta property="og:image"       content="${esc(image)}">
  <meta property="og:type"        content="website">
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="${esc(title)}">
  <meta name="twitter:description" content="${esc(bio)}">
  <meta name="twitter:image"       content="${esc(image)}">
  <meta http-equiv="refresh" content="0;url=${esc(url)}">
</head>
<body>
  <p>Redirecting to <a href="${esc(url)}">${esc(url)}</a>…</p>
</body>
</html>`);
};

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
