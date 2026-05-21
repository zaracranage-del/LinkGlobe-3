// /api/stripe-webhook.js — v5 zero-dep
const crypto = require('crypto');

function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', c => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

function verifyStripeSignature(rawBody, sigHeader, secret) {
  const parts = {};
  sigHeader.split(',').forEach(part => {
    const [k, ...v] = part.split('=');
    if (k === 't') parts.t = v.join('=');
    if (k === 'v1') parts.v1 = v.join('=');
  });
  if (!parts.t || !parts.v1) throw new Error('Invalid sig header');
  const signed = `${parts.t}.${rawBody}`;
  const expected = crypto.createHmac('sha256', secret).update(signed, 'utf8').digest('hex');
  if (expected !== parts.v1) throw new Error('Signature mismatch');
  const age = Math.floor(Date.now() / 1000) - parseInt(parts.t, 10);
  if (age > 300) throw new Error('Timestamp too old');
  return JSON.parse(rawBody);
}

async function stripeGet(path) {
  const r = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${process.env.STRIPE_SECRET_KEY}` },
  });
  if (!r.ok) throw new Error(`Stripe ${r.status} for ${path}`);
  return r.json();
}

function sbH() {
  return {
    'Content-Type': 'application/json',
    'apikey': process.env.SUPABASE_SERVICE_KEY,
    'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_KEY}`,
  };
}

async function sbPatch(table, data, col, val) {
  const r = await fetch(
    `${process.env.SUPABASE_URL}/rest/v1/${table}?${col}=eq.${encodeURIComponent(val)}`,
    { method: 'PATCH', headers: { ...sbH(), 'Prefer': 'return=minimal' }, body: JSON.stringify(data) }
  );
  if (!r.ok) throw new Error(`Supabase PATCH ${table} ${r.status}`);
}

async function sbGet(table, col, val) {
  const r = await fetch(
    `${process.env.SUPABASE_URL}/rest/v1/${table}?${col}=eq.${encodeURIComponent(val)}&limit=1`,
    { headers: { ...sbH(), 'Prefer': 'return=representation' } }
  );
  if (!r.ok) return null;
  const rows = await r.json();
  return rows[0] || null;
}

async function sbUpsert(table, data, conflict) {
  await fetch(
    `${process.env.SUPABASE_URL}/rest/v1/${table}?on_conflict=${conflict}`,
    { method: 'POST', headers: { ...sbH(), 'Prefer': 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify(data) }
  );
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const sig    = req.headers['stripe-signature'];
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!sig || !secret) return res.status(400).json({ error: 'Missing sig or secret' });

  let event;
  try {
    const raw = await getRawBody(req);
    event = verifyStripeSignature(raw, sig, secret);
  } catch (err) {
    return res.status(400).json({ error: err.message });
  }

  const PLAN_MAP = {
    [process.env.STRIPE_CREATOR_PRICE_ID]: 'creator',
    [process.env.STRIPE_PRO_PRICE_ID]:     'pro',
  };

  try {
    if (event.type === 'checkout.session.completed') {
      const s     = event.data.object;
      const email = s.customer_details?.email || s.metadata?.email;
      let priceId = s.metadata?.price_id;
      if (!priceId) {
        try {
          const items = await stripeGet(`/checkout/sessions/${s.id}/line_items?limit=1`);
          priceId = items.data?.[0]?.price?.id;
        } catch (e) { console.error('line_items:', e.message); }
      }
      const plan = PLAN_MAP[priceId] || (s.metadata?.plan === 'creator' || s.metadata?.plan === 'pro' ? s.metadata.plan : null);
      if (email && plan) {
        await sbPatch('signups', { plan }, 'email', email);
        const user = await sbGet('signups', 'email', email);
        if (user?.referred_by) {
          const ref = await sbGet('signups', 'ref_code', user.referred_by);
          if (ref?.email) await sbUpsert('referrals', { referrer_email: ref.email, referred_email: email, referred_plan: plan }, 'referred_email');
        }
        console.log(`checkout.session.completed: ${email} → ${plan}`);
      } else {
        console.warn('Could not determine plan', { email, priceId });
      }
    }

    if (event.type === 'customer.subscription.updated') {
      const sub = event.data.object;
      const priceId = sub.items?.data?.[0]?.price?.id;
      const plan = PLAN_MAP[priceId];
      if (plan) {
        const c = await stripeGet(`/customers/${sub.customer}`);
        if (c.email) await sbPatch('signups', { plan }, 'email', c.email);
      }
    }

    if (event.type === 'customer.subscription.deleted') {
      const c = await stripeGet(`/customers/${event.data.object.customer}`);
      if (c.email) await sbPatch('signups', { plan: 'free' }, 'email', c.email);
    }

    if (event.type === 'invoice.payment_failed') {
      const c = await stripeGet(`/customers/${event.data.object.customer}`);
      console.log(`Payment failed: ${c.email}`);
    }

    return res.status(200).json({ received: true });
  } catch (err) {
    console.error('webhook error:', err.message);
    return res.status(500).json({ error: err.message });
  }
};
