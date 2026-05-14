const express = require('express');
const geoip = require('geoip-lite');
const app = express();

const amazonStores = {
  AU: 'https://www.amazon.com.au',
  GB: 'https://www.amazon.co.uk',
  DE: 'https://www.amazon.de',
  FR: 'https://www.amazon.fr',
  CA: 'https://www.amazon.ca',
  JP: 'https://www.amazon.co.jp',
  IN: 'https://www.amazon.in',
  US: 'https://www.amazon.com',
};

const AD_PARAMS = ['gclid','gclsrc','gad_source','gad_campaignid','gbraid','dxid',
                   'dxgaid','utm_source','utm_medium','utm_campaign','utm_term',
                   'utm_content','fbclid','msclkid','twclid'];

// Fetch product OG image server-side (no CORS restrictions)
app.get('/api/og', async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=86400');
  const { url } = req.query;
  if (!url) return res.json({ image: '' });
  try {
    const u = new URL(url);
    AD_PARAMS.forEach(p => u.searchParams.delete(p));
    const cleanUrl = u.toString();
    const response = await fetch(cleanUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-AU,en;q=0.9'
      },
      signal: AbortSignal.timeout(8000),
      redirect: 'follow'
    });
    if (!response.ok) return res.json({ image: '' });
    const html = await response.text();
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
    const ldMatch = html.match(/"image"\s*:\s*"(https?:\/\/[^"]+)"/);
    if (ldMatch) return res.json({ image: ldMatch[1] });
    return res.json({ image: '' });
  } catch (e) {
    return res.json({ image: '' });
  }
});

app.get('/redirect', (req, res) => {
  const { asin, tag } = req.query;
  const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
  const geo = geoip.lookup(ip);
  const country = geo ? geo.country : 'US';
  const store = amazonStores[country] || amazonStores['US'];
  const redirectUrl = `${store}/dp/${asin}?tag=${tag}`;
  console.log(`Visitor from ${country} → redirecting to ${redirectUrl}`);
  res.redirect(redirectUrl);
});

app.get('/', (req, res) => {
  res.send(`
    <h1>🌏 LinkRedirect</h1>
    <p>Smart affiliate links for global audiences.</p>
    <p>Usage: /redirect?asin=PRODUCT_ID&tag=YOUR_AFFILIATE_TAG</p>
  `);
});

app.listen(3000, () => {
  console.log('LinkRedirect is running on http://localhost:3000');
});
