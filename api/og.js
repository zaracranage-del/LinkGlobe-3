// Serverless function — fetches OG images server-side (no CORS issues)
const AD_PARAMS = ['gclid','gclsrc','gad_source','gad_campaignid','gbraid','dxid',
                   'dxgaid','utm_source','utm_medium','utm_campaign','utm_term',
                   'utm_content','fbclid','msclkid','twclid'];

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=86400'); // cache 24h

  const { url } = req.query;
  if (!url) return res.status(400).json({ image: '' });

  let cleanUrl;
  try {
    const u = new URL(url);
    AD_PARAMS.forEach(p => u.searchParams.delete(p));
    cleanUrl = u.toString();
  } catch { return res.json({ image: '' }); }

  try {
    const response = await fetch(cleanUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-AU,en;q=0.9'
      },
      signal: AbortSignal.timeout(8000),
      redirect: 'follow'
    });

    if (!response.ok) return res.json({ image: '' });
    const html = await response.text();

    // og:image or twitter:image meta tags
    const patterns = [
      /<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/i,
      /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image["']/i,
      /<meta[^>]+name=["']twitter:image["'][^>]+content=["']([^"']+)["']/i,
      /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']twitter:image["']/i,
    ];
    for (const re of patterns) {
      const m = html.match(re);
      if (m && m[1] && m[1].startsWith('http')) return res.json({ image: m[1] });
    }

    // JSON-LD structured data
    const ldMatch = html.match(/"image"\s*:\s*"(https?:\/\/[^"]+)"/);
    if (ldMatch) return res.json({ image: ldMatch[1] });

    return res.json({ image: '' });
  } catch (e) {
    return res.json({ image: '' });
  }
};
