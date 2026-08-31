/**
 * routes/forecastBatch.js
 * POST /api/forecast-batch  –  proxies a batch of invoices to the ML
 *                              /predict-batch endpoint and returns the
 *                              full summary: results, match_rate, etc.
 */

const express = require('express');
const router = express.Router();

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5001';

router.post('/', async (req, res) => {
  const batch = req.body;

  if (!Array.isArray(batch) || batch.length === 0) {
    return res.status(400).json({ error: 'Request body must be a non-empty array of invoices' });
  }

  try {
    const mlResponse = await fetch(`${ML_SERVICE_URL}/predict-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch),
    });

    if (!mlResponse.ok) {
      const errorBody = await mlResponse.json().catch(() => ({}));
      return res.status(502).json({ error: 'ML service returned an error', detail: errorBody });
    }

    const summary = await mlResponse.json();
    return res.json(summary);

  } catch (err) {
    console.error('[forecast-batch route] ML service unreachable:', err.message);
    return res.status(503).json({
      error: 'ML service is unavailable. Is Flask running on port 5001?',
    });
  }
});

module.exports = router;
