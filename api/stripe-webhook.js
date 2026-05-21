const Stripe = require('stripe');
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const PLAN_MAP = {
  [process.env.STRIPE_CREATOR_PRICE_ID]: 'creator',
  [process.env.STRIPE_PRO_PRICE_ID]: 'pro',
};

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const sig = req.headers['stripe-signature'];
  let event;

  try {
    const raw = await getRawBody(req);
    event = stripe.webhooks.constructEvent(raw, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    console.error('Webhook signature failed:', err.message);
    return res.status(400).json({ error: `Webhook error: ${err.message}` });
  }

  try {
    if (event.type === 'checkout.session.completed') {
      const session = event.data.object;
      const email = session.customer_details?.email || session.metadata?.email;

      // line_items aren't included in webhook payloads by default — retrieve them
      let priceId = session.metadata?.price_id;
      if (!priceId) {
        try {
          const full = await stripe.checkout.sessions.retrieve(session.id, {
            expand: ['line_items'],
          });
          priceId = full.line_items?.data?.[0]?.price?.id;
        } catch (e) {
          console.error('Could not expand line_items:', e.message);
        }
      }

      const plan = PLAN_MAP[priceId] || derivePlanFromMetadata(session.metadata);

      if (email && plan) {
        await supabase.from('signups').update({ plan }).eq('email', email);
        console.log(`Upgraded ${email} to ${plan}`);

        // Record referral if this user was referred
        const { data: newUser } = await supabase
          .from('signups').select('referred_by').eq('email', email).single();
        if (newUser?.referred_by) {
          // Find referrer's email by their ref_code
          const { data: referrer } = await supabase
            .from('signups').select('email').eq('ref_code', newUser.referred_by).single();
          if (referrer?.email) {
            // Upsert so re-upgrades just update the plan
            await supabase.from('referrals').upsert({
              referrer_email: referrer.email,
              referred_email: email,
              referred_plan: plan,
            }, { onConflict: 'referred_email' });
            console.log(`Referral recorded: ${referrer.email} → ${email} (${plan})`);
          }
        }
      } else {
        console.warn('checkout.session.completed — could not determine plan', {
          email, priceId, plan, metadata: session.metadata,
        });
      }
    }

    if (event.type === 'customer.subscription.updated') {
      const sub = event.data.object;
      const customer = await stripe.customers.retrieve(sub.customer);
      const email = customer.email;
      if (email && sub.items?.data?.[0]?.price?.id) {
        const priceId = sub.items.data[0].price.id;
        const plan = PLAN_MAP[priceId];
        if (plan) {
          await supabase.from('signups').update({ plan }).eq('email', email);
          console.log(`Plan updated for ${email} → ${plan}`);
        }
      }
    }

    if (event.type === 'customer.subscription.deleted') {
      const sub = event.data.object;
      const customer = await stripe.customers.retrieve(sub.customer);
      const email = customer.email;
      if (email) {
        await supabase.from('signups').update({ plan: 'free' }).eq('email', email);
        console.log(`Downgraded ${email} to free`);
      }
    }

    if (event.type === 'invoice.payment_failed') {
      const invoice = event.data.object;
      const customer = await stripe.customers.retrieve(invoice.customer);
      const email = customer.email;
      if (email) {
        console.log(`Payment failed for ${email} — plan kept until subscription ends`);
      }
    }

    return res.status(200).json({ received: true });
  } catch (err) {
    console.error('Webhook handler error:', err);
    return res.status(500).json({ error: 'Internal error' });
  }
};

function derivePlanFromMetadata(metadata) {
  if (!metadata) return null;
  const p = metadata.plan;
  if (p === 'creator' || p === 'pro') return p;
  return null;
}

function getRawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}
