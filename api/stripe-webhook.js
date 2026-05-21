// /api/stripe-webhook.js
// Zero npm dependencies — uses Node built-in crypto + native fetch
// Works on Vercel Node 20 runtime without any npm install

const crypto = require('crypto');

// ── Stripe signature verification ───────────────────────────────
function verifyStripeSignature(rawBody, sigHeader, secret) {
  const parts = {};
  sigHeader.split(',').forEach(part => {
    const [k, v] = part.split('=');
    if (k === 't') parts.t = v;
    if (k === 'v1') parts.v1 = v;
  });
  if (!parts.t || !parts.v1) throw new Error('Invalid signature header');

  const signed = `${parts.t}.${rawBody}`;
  const expected = crypto.createHmac('sha256', secret).update(signed).digest('hex');
  const safe = crypto.timingSafeEqual(Buffer.from(expected, 'hex'), Buffer.from(parts.v1, 'hex'));
  if (!safe) throw new Error('Signature mismatch');

  const age = Math.floor(Date.now() / 1000) - parseInt(parts.t, 10);
  if (age > 300) throw new Error('Timestamp too old');

  return JSON.parse(rawBody);
}

// ── Stripe REST helpers ──────────────────────────────────────────
async function stripeGet(path) {
  const res = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${process.env.STRIPE_SECRET_KEY}` },
  });
  if (!res.ok) throw new Error(`Stripe ${path} → ${res.status}`);
  return res.json();
}

// ── Supabase REST helpers ────────────────────────────────────────
const SB_URL = () => process.env.SUPABASE_URL;
const SB_KEY = () => process.env.SUPABASE_SERVICE_KEY;

function sbHeaders() {
  return {
    'Content-Type': 'application/json',
    'apikey': SB_KEY(),
    'Authorization': `Bearer ${SB_KEY()}`,
    'Prefer': 'return=minimal',
  };
}

async function sbUpdate(table, data, col, val) {
  const res = await fetch(`${SB_URL()}/rest/v1/${table}?${col}=eq.${encodeURIComponent(val)}`, {
    method: 'PATCH',
    headers: sbHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase PATCH ${table}: ${res.status} ${text}`);
  }
  return res;
}

async function sbSelect(table, col, val) {
  const res = await fetch(`${SB_URL()}/rest/v1/${table}?${col}=eq.${encodeURIComponent(val)}&limit=1`, {
    headers: { ...sbHeaders(), 'Prefer': 'return=representation' },
  });
  if (!res.ok) return null;
  const rows = await res.json();
  return rows[0] || null;
}

async function sbUpsert(table, data, onConflict) {
  const res = await fetch(`${SB_URL()}/rest/v1/${table}?on_conflict=${onConflict}`, {
    method: 'POST',
    headers: { ...sbHeaders(), 'Prefer': 'resolution=merge-duplicates,return=minimal' },
    body: JSON.stringify(data),
  });
  return res;
}

// ── Plan map (resolved at request time so env vars are available) ─
function planMap() {
  return {
    [process.env.STRIPE_CREATOR_PRICE_ID]: 'creator',
    [process.env.STRIPE_PRO_PRICE_ID]: 'pro',
  };
}

// ── Raw body reader ──────────────────────────────────────────────
function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', c => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

// ── Main handler ─────────────────────────────────────────────────
module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const sig = req.headers['stripe-signature'];
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!sig || !secret) {
    return res.status(400).json({ error: 'Missing signature or webhook secret' });
  }

  let event;
  try {
    const raw = await getRawBody(req);
    event = verifyStripeSignature(raw, sig, secret);
  } catch (err) {
    console.error('Signature failed:', err.message);
    return res.status(400).json({ error: `Webhook error: ${err.message}` });
  }

  try {
    const map = planMap();

    // ── checkout.session.completed ──────────────────────────────
    if (event.type === 'checkout.session.completed') {
      const session = event.data.object;
      const email = session.customer_details?.email || session.metadata?.email;

      let priceId = session.metadata?.price_id;
      if (!priceId) {
        try {
          const items = await stripeGet(`/checkout/sessions/${session.id}/line_items?limit=1`);
          priceId = items.data?.[0]?.price?.id;
        } catch (e) {
          console.error('line_items fetch failed:', e.message);
        }
      }

      const plan = map[priceId] || (session.metadata?.plan === 'creator' || session.metadata?.plan === 'pro' ? session.metadata.plan : null);

      if (email && plan) {
        await sbUpdate('signups', { plan }, 'email', email);
        console.log(`Upgraded ${email} to ${plan}`);

        const user = await sbSelect('signups', 'email', email);
        if (user?.referred_by) {
          const referrer = await sbSelect('signups', 'ref_code', user.referred_by);
          if (referrer?.email) {
            await sbUpsert('referrals', {
              referrer_email: referrer.email,
              referred_email: email,
              referred_plan: plan,
            }, 'referred_email');
            console.log(`Referral: ${referrer.email} → ${email} (${plan})`);
          }
        }
      } else {
        console.warn('Could not determine plan', { email, priceId, plan });
      }
    }

    // ── customer.subscription.updated ──────────────────────────
    if (event.type === 'customer.subscription.updated') {
      const sub = event.data.object;
      const priceId = sub.items?.data?.[0]?.price?.id;
      const plan = map[priceId];
      if (plan) {
        const customer = await stripeGet(`/customers/${sub.customer}`);
        if (customer.email) {
          await sbUpdate('signups', { plan }, 'email', customer.email);
          console.log(`Plan updated: ${customer.email} → ${plan}`);
        }
      }
    }

    // ── customer.subscription.deleted ──────────────────────────
    if (event.type === 'customer.subscription.deleted') {
      const sub = event.data.object;
      const customer = await stripeGet(`/customers/${sub.customer}`);
      if (customer.email) {
        await sbUpdate('signups', { plan: 'free' }, 'email', customer.email);
        console.log(`Downgraded ${customer.email} to free`);
      }
    }

    // ── invoice.payment_failed ──────────────────────────────────
    if (event.type === 'invoice.payment_failed') {
      const invoice = event.data.object;
      const customer = await stripeGet(`/customers/${invoice.customer}`);
      if (customer.email) {
        console.log(`Payment failed: ${customer.email}`);
      }
    }

    return res.status(200).json({ received: true });
  } catch (err) {
    console.error('Handler error:', err.message, err.stack);
    return res.status(500).json({ error: err.message });
  }
};
