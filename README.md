# Invoice Payment Forecaster

> ML-powered prediction of invoice payment delays with risk-based collections prioritization.

---

## The Problem

Most accounts-receivable systems track invoices by their due date — implicitly assuming every customer will pay on time. In practice, payment behavior varies significantly across customer segments, invoice sizes, and individual payment histories.

This creates two compounding problems:

1. **Cash-flow forecasts are inaccurate.** Finance teams plan around due dates, not realistic receipt dates — leading to liquidity surprises when high-value customers pay late.
2. **Collections are reactive, not proactive.** Without a delay signal ahead of the due date, teams work random queues rather than focusing effort where late payment is most likely.

A due date is not a payment date.

---

## The Solution

Invoice Payment Forecaster replaces due-date thinking with a machine learning model that predicts, *before* an invoice becomes overdue, how many days late it is likely to be paid.

Each invoice is scored and classified into a risk tier:

| Risk Level | Predicted Delay | Action |
|---|---|---|
| 🔴 **HIGH** | > 10 days | Priority outreach |
| 🟡 **MEDIUM** | 3 – 10 days | Monitor closely |
| 🟢 **LOW** | < 3 days | Routine follow-up |

The dashboard also surfaces a **plain-English reason** for each prediction (e.g. *"Flagged HIGH: customer has a history of significant delays and a large invoice amount."*) and a **Forecast Comparison** card showing the gap between the naive on-time assumption and the ML-adjusted cash-flow expectation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS v3 |
| **Backend API** | Node.js, Express 5, dotenv, CORS |
| **ML Service** | Python 3, Flask, flask-cors, scikit-learn, pandas |
| **Data** | Synthetic dataset (1 000 invoices) generated with Faker |

### Architecture

```
React Dashboard  :5173
       │
       │  POST /api/forecast
       ▼
Express API  :5000
       │
       │  POST /predict
       ▼
Flask ML Service  :5001
       │
       │  loads forecast_model.pkl
       ▼
sklearn Pipeline (OneHotEncoder → LinearRegression)
```

---

## The Model

**Algorithm:** Linear Regression with a scikit-learn `Pipeline`

**Features:**

| Feature | Type | Description |
|---|---|---|
| `customer_segment` | Categorical (OHE) | SMB / Enterprise / Startup / Government |
| `invoice_amount` | Numeric | Invoice value in USD |
| `customer_avg_past_delay` | Numeric | Customer's historical average payment delay (days) |

**Target:** `days_late` — number of days after the due date the invoice was paid

**Train / test split:** 80 / 20

### Performance

Evaluated on 200 held-out invoices:

| Metric | Score |
|---|---|
| **MAE** (Mean Absolute Error) | **3.40 days** |
| **RMSE** (Root Mean Squared Error) | **4.22 days** |

---

## Key Features

- **Risk classification** — every prediction is bucketed into HIGH / MEDIUM / LOW with color-coded table rows and badges
- **Explainability** — a short human-readable reason accompanies each prediction, flagging the dominant drivers (payment history, invoice size, or segment baseline)
- **Forecast comparison** — summary card contrasting the naive on-time assumption against the ML-adjusted average delay across all submitted invoices
- **Sorted results table** — HIGH-risk invoices always surface at the top, regardless of submission order

---

## Known Limitation

**Linear regression extrapolates poorly on out-of-range invoice amounts.**

Linear models extend their learned slope indefinitely. For very large invoice amounts outside the training distribution, the model can produce unrealistically high (or negative) predictions.

**Current safeguard:** predictions are clamped to **[0, 90] days** in `ml/app.py`:

```python
days = min(90.0, max(0.0, float(raw_pred)))
```

**Production fix:** replace the linear model with a tree-based model such as `RandomForestRegressor` or `XGBRegressor`, which naturally avoids extrapolation and handles non-linear interactions between segment, amount, and history.

---

## Project Structure

```
invoice-forecaster/
├── backend/
│   ├── src/
│   │   ├── index.js              # Express entry point (port 5000)
│   │   └── routes/
│   │       └── forecast.js       # POST /api/forecast → proxies to Flask
│   ├── .env.example
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Dashboard UI (form, cards, table)
│   │   └── index.css             # Tailwind directives + reset
│   ├── tailwind.config.js
│   └── package.json
│
├── ml/
│   ├── app.py                    # Flask ML service (port 5001)
│   ├── train_model.py            # Training script → forecast_model.pkl
│   ├── generate_data.py          # Synthetic data generator → invoices.csv
│   ├── forecast_model.pkl        # Trained sklearn Pipeline
│   ├── invoices.csv              # 1 000-row dataset
│   └── requirements.txt
│
├── README.md
└── PROGRESS.md
```

---

## Running Locally

You need **Node.js ≥ 18** and **Python ≥ 3.10**. MongoDB is optional — the Express server starts without it.

### 1 · ML Service (Flask) — port 5001

```bash
cd ml

# First time only
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# Generate data and train the model (first time only)
python generate_data.py
python train_model.py

# Start the service
python app.py
```

### 2 · Backend API (Express) — port 5000

```bash
cd backend
cp .env.example .env   # edit MONGO_URI if needed
npm install
npm start
```

### 3 · Frontend (React + Vite) — port 5173

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. All three services must be running for predictions to work.

### Quick smoke test

```bash
# Hit Flask directly
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_segment":"Government","invoice_amount":120000,"customer_avg_past_delay":22}'

# Hit Express (the route the UI uses)
curl -X POST http://localhost:5000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"customer_segment":"SMB","invoice_amount":45000,"customer_avg_past_delay":8.5}'
```

Expected response:

```json
{
  "predicted_days_late": 8.91,
  "risk_level": "MEDIUM",
  "reason": "Flagged MEDIUM: prediction is based on the SMB segment baseline."
}
```

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Express server port |
| `MONGO_URI` | `mongodb://localhost:27017/invoice-forecaster` | MongoDB connection string |
| `ML_SERVICE_URL` | `http://localhost:5001` | Flask service base URL |

---

## Future Improvements

### Model & Data
- [ ] **Tree-based model** — replace Linear Regression with Random Forest or XGBoost to eliminate extrapolation issues and capture non-linear interactions
- [ ] **Default-risk classification** — binary logistic regression model predicting whether an invoice will default entirely, not just how late it pays
- [ ] **Real invoice data integration** — connect to QuickBooks, Xero, or SAP APIs to train on actual customer payment history
- [ ] **Richer features** — add `days_until_due`, `outstanding_balance`, `invoice_age`, and seasonality signals
- [ ] **Model retraining pipeline** — scheduled job that retrains on new data and hot-swaps the pkl without downtime

### Backend & Infrastructure
- [ ] **MongoDB persistence** — store submitted invoices and predictions for audit trails and retraining pipelines
- [ ] **Authentication** — JWT-based auth so each team sees only their own data
- [ ] **Docker Compose** — single `docker-compose up` to start all three services
- [ ] **Rate limiting and input sanitization** — harden the public-facing Express API

### Frontend
- [ ] **Collections Kanban** — drag invoices through *Pending → Contacted → Resolved* stages
- [ ] **Analytics page** — bar charts of predicted delay by segment, risk distribution over time
- [ ] **CSV bulk import** — paste or upload a spreadsheet of invoices for batch forecasting
- [ ] **PDF / Excel export** — download the risk-sorted table for reporting

---

## License

MIT
