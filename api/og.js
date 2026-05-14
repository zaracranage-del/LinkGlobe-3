const AD_PARAMS = ['gclid','gclsrc','gad_source','gad_campaignid','gbraid','dxid',
                   'dxgaid','utm_source','utm_medium','utm_campaign','utm_term',
                   'utm_content','fbclid','msclkid','twclid'];

function extractAsin(url) {
  const m = url.match(/\/dp\/([A-Z0-9]{10})|\/gp\/product\/([A-Z0-9]{10})|\/ASIN\/([A-Z0-9]{10})/i);
  return m ? (m[1] || m[2] || m[3]) : null;
}

const DESKTOP_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const MOBILE_UA  = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1';

function browserHeaders(ua) {
  return {
    'User-Agent': ua,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
  };
}

async function getAmazonImage(asin) {
  // Amazon affiliate image widget — designed to be fetched from anywhere, no bot-detection
  const widgetUrl = `https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN=${asin}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=_SL500_`;
  try {
    const r = await fetch(widgetUrl, {
      headers: { ...browserHeaders(DESKTOP_UA), 'Referer': 'https://www.amazon.com/' },
      signal: AbortSignal.timeout(6000),
      redirect: 'follow',
    });
    if (!r.ok) return '';
    const html = await r.text();
    const m = html.match(/src=["'](https?:\/\/[^"']*\.(?:jpg|jpeg|png|webp))[^"']*/i);
    return m ? m[1] : '';
  } catch { return ''; }
}

function extractFromHtml(html, baseUrl) {
  // og:image / twitter:image meta tags
  const patterns = [
    /<meta[^>]+property=["']og:image(?::url)?["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:image(?::url)?["']/i,
    /<meta[^>]+name=["']twitter:image(?::src)?["'][^>]+content=["']([^"']+)["']/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']twitter:image(?::src)?["']/i,
  ];
  for (const re of patterns) {
    const m = html.match(re);
    if (m && m[1]) {
      const src = m[1].startsWith('//') ? 'https:' + m[1]
                : m[1].startsWith('/')  ? new URL(m[1], baseUrl).href
                : m[1];
      if (src.startsWith('http')) return src;
    }
  }

  // JSON-LD structured data (Shopify, brand sites, Charlotte Tilbury etc.)
  for (const block of html.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    try {
      const j = JSON.parse(block[1]);
      const nodes = Array.isArray(j['@graph']) ? j['@graph'] : [j];
      for (const n of nodes) {
        const img = n.image;
        if (!img) continue;
        const src = Array.isArray(img) ? img[0] : (typeof img === 'string' ? img : img.url || img['@id']);
        if (src && typeof src === 'string' && src.startsWith('http')) return src;
      }
    } catch {}
  }

  // Shopify product JSON embedded in page
  const shopifyMatch = html.match(/"featured_image"\s*:\s*"(https?:[^"]+)"/);
  if (shopifyMatch) return shopifyMatch[1].replace(/\\u0026/g, '&');

  return '';
}

async function getOgImage(url) {
  // Try desktop UA first, then mobile UA — some WAFs block one but not the other
  for (const ua of [DESKTOP_UA, MOBILE_UA]) {
    try {
      const r = await fetch(url, {
        headers: browserHeaders(ua),
        signal: AbortSignal.timeout(8000),
        redirect: 'follow',
      });
      if (!r.ok) continue;
      const html = await r.text();
      const img = extractFromHtml(html, url);
      if (img) return img;
    } catch {}
  }
  return '';
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=86400');

  const { url } = req.query;
  if (!url) return res.status(400).json({ image: '' });

  let cleanUrl;
  try {
    const u = new URL(url);
    AD_PARAMS.forEach(p => u.searchParams.delete(p));
    cleanUrl = u.toString();
  } catch { return res.json({ image: '' }); }

  // Amazon: affiliate widget bypasses bot detection entirely
  const asin = extractAsin(cleanUrl);
  if (asin) {
    const img = await getAmazonImage(asin);
    if (img) return res.json({ image: img });
    // Fall through to OG scrape if widget fails
  }

  // Brand sites: try desktop then mobile UA
  const img = await getOgImage(cleanUrl);
  return res.json({ image: img });
};
