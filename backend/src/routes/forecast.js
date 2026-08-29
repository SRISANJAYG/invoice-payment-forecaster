/**
 * routes/forecast.js
 * POST /api/forecast  –  proxies invoice data to the ML service and
 *                        returns the predicted days_late + risk_level.
 */

const express = require('express');
const router = express.Router();

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5001';

router.post('/', async (req, res) => {
  const { customer_segment, invoice_amount, customer_avg_past_delay } = req.body;

  // ── Basic validation ────────────────────────────────────────────────────────
  const missing = [];
  if (!customer_segment)            missing.push('customer_segment');
  if (invoice_amount == null)       missing.push('invoice_amount');
  if (customer_avg_past_delay == null) missing.push('customer_avg_past_delay');

  if (missing.length) {
    return res.status(400).json({ error: `Missing fields: ${missing.join(', ')}` });
  }

  // ── Call ML microservice ────────────────────────────────────────────────────
  try {
    const mlResponse = await fetch(`${ML_SERVICE_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_segment, invoice_amount, customer_avg_past_delay }),
    });

    if (!mlResponse.ok) {
      const errorBody = await mlResponse.json().catch(() => ({}));
      return res.status(502).json({
        error: 'ML service returned an error',
        detail: errorBody,
      });
    }

    const prediction = await mlResponse.json();
    return res.json(prediction);

  } catch (err) {
    console.error('[forecast route] ML service unreachable:', err.message);
    return res.status(503).json({
      error: 'ML service is unavailable. Is Flask running on port 5001?',
    });
  }
});

module.exports = router;
