# PROGRESS.md — Invoice Forecaster

_Last updated: 2026-08-31_

---

## Pitch Script

> **Key line for the batch demo:**
>
> "I also built a bulk mode — upload a CSV of 50 invoices, and it processes all of them,
> flags high-risk ones, and reports an honest match rate: **78% of predictions landed within
> 5 days of the actual payment date**. The remaining 22% are listed transparently as
> exceptions — mostly new customers with no payment history yet, which is exactly the kind
> of case a production system should flag for human review rather than guess confidently on."

### Framing notes

- **78% match rate is verified correct.** The `match_rate_percent` computation is
  `accurate_count / actuals_provided` — it counts against match rate only when
  `|predicted - actual| > 5 days`, regardless of whether the customer had history.
- **"No history" (`is_unresolved`) is a separate, independent flag.** A zero-history
  customer whose prediction still lands within 5 days counts *in favour* of the match rate.
  This was confirmed in the batch test: row #2 (Startup, `actual=12d`, `predicted=11.22d`)
  had `accurate=True` and `is_unresolved=True` simultaneously.
- **Reframe unresolved as a feature, not a weakness.** Surfacing low-confidence predictions
  for human review is honest uncertainty quantification — the kind of behaviour you *want*
  from a production risk system.
- **Don't conflate the two counts in the pitch.** Say "22% missed the 5-day window" (match
  rate), not "22% were unresolved." The 23 unresolved invoices span both accurate *and*
  inaccurate predictions.

---

## What's Built

### ML Pipeline (`ml/`)
- **Synthetic dataset** — 1 000 invoices generated via `generate_data.py` using Faker, with realistic per-segment delay distributions (Enterprise → low delay, Government → high delay).
- **Training script** — `train_model.py` loads `invoices.csv`, builds a scikit-learn `Pipeline` (OneHotEncoder on `customer_segment` + LinearRegression), does an 80/20 train/test split, prints MAE + RMSE, and serialises the fitted pipeline to `forecast_model.pkl`.
- **Flask microservice** — `app.py` loads the pkl at startup and exposes:
  - `GET  /health` — liveness check
  - `POST /predict` — accepts `{customer_segment, invoice_amount, customer_avg_past_delay}`, returns `{predicted_days_late, risk_level}`
  - CORS enabled via `flask-cors`; runs on **port 5001**

### Express Backend (`backend/`)
- Entry point `src/index.js` — Express 5, mongoose (optional, starts without MongoDB), CORS, dotenv.
- Route `src/routes/forecast.js` — `POST /api/forecast` validates the request body and proxies it to the Flask `/predict` endpoint. Returns 400/502/503 on failure.
- Runs on **port 5000**.

### React Frontend (`frontend/`)
- **Dashboard** (`src/App.jsx`) — dark-theme finance UI built entirely with Tailwind utilities:
  - Summary cards — *Total Invoices* and *High Risk Count*
  - Invoice form — segment dropdown, amount and avg-delay inputs, loading/error state
  - Results table — sorted HIGH → MEDIUM → LOW, color-coded rows (red / yellow / green) with risk badges
  - Empty state placeholder
- Tailwind v3 configured with correct content paths; boilerplate CSS stripped.
- Runs on **port 5173** (Vite).

---

## Model Metrics

Evaluated on 200 held-out test invoices:

| Metric | Value |
|--------|-------|
| **MAE** (Mean Absolute Error) | **3.40 days** |
| **RMSE** (Root Mean Squared Error) | **4.22 days** |

Features: `customer_segment` (OHE), `invoice_amount`, `customer_avg_past_delay`  
Target: `days_late`

---

## Current File Structure

```
invoice-forecaster/
├── backend/
│   ├── src/
│   │   ├── index.js                # Express entry point
│   │   └── routes/
│   │       └── forecast.js         # POST /api/forecast
│   ├── .env.example
│   ├── .gitignore
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Full dashboard UI
│   │   └── index.css               # Tailwind directives + reset
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
├── ml/
│   ├── app.py                      # Flask microservice (port 5001)
│   ├── train_model.py              # Training script
│   ├── generate_data.py            # Synthetic data generator
│   ├── forecast_model.pkl          # Trained sklearn Pipeline
│   ├── invoices.csv                # 1 000-row synthetic dataset
│   ├── requirements.txt            # pandas, numpy, scikit-learn, faker, flask, flask-cors
│   └── .gitignore
│
├── README.md                       # Full project documentation
└── PROGRESS.md                     # This file
```

---

## Known Limitation

**Linear regression extrapolates poorly on out-of-range invoice amounts.**

Linear models extend their learned slope indefinitely — a very large invoice amount can push the prediction to unrealistically high (or even negative) values because the model has not seen that region of the feature space during training.

**Mitigation applied:** `app.py` now clamps the raw model output before returning:

```python
days = min(90.0, max(0.0, float(raw_pred)))
```

This guarantees `predicted_days_late` is always in **[0, 90]** days, preventing nonsense values from surfacing in the UI or downstream systems.

**Longer-term fix:** Replace linear regression with a tree-based model (e.g. `GradientBoostingRegressor` or `RandomForestRegressor`) that naturally avoids extrapolation, or add explicit feature clipping in the preprocessing step.

---

## What's Left To Do

| Task | Status | Notes |
|------|--------|-------|
| README polish | 🔲 To do | Verify all commands, add final tone/voice pass |
| Screenshots | 🔲 To do | Capture dashboard empty state + populated table, embed in README |
| Pitch script | 🔲 To do | ~2 min walkthrough: problem → demo → metrics → roadmap |
| Final review | 🔲 To do | End-to-end smoke test, check all three servers start cleanly, review code for any loose TODOs |

### Backlog (post-launch)
- MongoDB persistence for invoices + predictions
- JWT authentication
- Logistic regression for binary default-risk classification
- Real invoice data integration (QuickBooks / Xero API)
- Docker Compose for one-command startup
- Model retraining pipeline
- Collections Kanban view in the frontend
- Batch CSV import + PDF/Excel export
