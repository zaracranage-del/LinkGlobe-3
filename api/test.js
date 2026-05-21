module.exports = (req, res) => {
  try {
    const stripe = require('stripe');
    res.status(200).json({ ok: true, stripe_loaded: true, stripe_version: stripe.VERSION || 'unknown' });
  } catch (e) {
    res.status(200).json({ ok: false, error: e.message });
  }
};
