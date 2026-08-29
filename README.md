# Invoice Forecaster

> **ML-powered payment delay prediction and risk-based collections prioritization.**

---

## The Problem

Most accounts-receivable systems track invoices only by their due date — treating every invoice as equally likely to be paid on time. In practice, payment behavior varies dramatically by customer segment, historical relationship, and invoice size.

This creates two costly blind spots:

- **Collections teams work random queues** instead of focusing effort where late payment is most probable.
- **Cash-flow forecasts assume on-time payment**, leading to liquidity surprises when high-value customers habitually pay late.

A due date is not a payment date.

---

## The Solution

Invoice Forecaster replaces due-date thinking with a **trained regression model** that predicts how many days late a given invoice is likely to be paid — before it becomes overdue.

Each submitted invoice is scored and assigned a risk tier:

| Risk Level | Predicted Delay |
|------------|----------------|
| 🔴 HIGH    | > 10 days late |
| 🟡 MEDIUM  | 3 – 10 days late |
| 🟢 LOW     | < 3 days late  |

Collections teams see a live dashboard sorted by risk, so the most at-risk invoices are always at the top of the queue.

---

## Tech Stack

| Layer        | Technology                                                        |
|--------------|-------------------------------------------------------------------|
| **Frontend** | React 18, Vite, Tailwind CSS v3                                   |
| **Backend**  | Node.js, Express 5, `node-fetch`, CORS, dotenv                    |
| **ML Service** | Python 3, Flask, flask-cors, scikit-learn, pandas, numpy        |
| **Model**    | Linear Regression with `OneHotEncoder` via sklearn `Pipeline`     |
| **Data**     | Synthetic dataset (1 000 invoices) generated with Faker           |

### Architecture

```
┌─────────────────────────────┐
│  React Dashboard  :5173     │  ← Invoice form + risk table
└────────────┬────────────────┘
             │ POST /api/forecast
┌────────────▼────────────────┐
│  Express API      :5000     │  ← Input validation, proxy layer
└────────────┬────────────────┘
             │ POST /predict
┌────────────▼────────────────┐
│  Flask ML Service :5001     │  ← Loads forecast_model.pkl, returns
│                             │    predicted_days_late + risk_level
└─────────────────────────────┘
```

---

## Model Performance

The model was trained on 800 invoices and evaluated on a held-out test set of 200 invoices.

| Metric | Score |
|--------|-------|
| **MAE** (Mean Absolute Error) | **3.40 days** |
| **RMSE** (Root Mean Squared Error) | **4.22 days** |

**Features used:**

- `customer_segment` — OneHot encoded (SMB / Enterprise / Startup / Government)
- `invoice_amount` — raw dollar value
- `customer_avg_past_delay` — historical average payment delay for this customer

**Target:** `days_late` — how many days after the due date the invoice was paid.

---

## Project Structure

```
invoice-forecaster/
├── backend/
│   ├── src/
│   │   ├── index.js            # Express entry point (port 5000)
│   │   └── routes/
│   │       └── forecast.js     # POST /api/forecast → proxies to Flask
│   ├── .env.example
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Dashboard: form + summary cards + risk table
│   │   └── index.css           # Tailwind directives + minimal reset
│   ├── tailwind.config.js
│   └── package.json
│
├── ml/
│   ├── app.py                  # Flask microservice (port 5001)
│   ├── train_model.py          # Training script → saves forecast_model.pkl
│   ├── generate_data.py        # Synthetic data generator → invoices.csv
│   ├── forecast_model.pkl      # Trained sklearn Pipeline (committed for convenience)
│   ├── invoices.csv            # Generated dataset (1 000 rows)
│   └── requirements.txt
│
└── README.md
```

---

## Running Locally

You need **Node.js ≥ 18**, **Python ≥ 3.10**, and optionally **MongoDB** (the backend starts without it).

### 1 · ML Service (Flask)

```bash
cd ml

# First time only
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# Generate training data and train the model (first time only)
python generate_data.py
python train_model.py

# Start the ML service
python app.py
# → http://localhost:5001
```

### 2 · Backend (Express)

```bash
cd backend
cp .env.example .env           # edit MONGO_URI if needed
npm install
npm start
# → http://localhost:5000
```

### 3 · Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Open **http://localhost:5173** — all three services must be running for end-to-end predictions to work.

### Quick API test

```bash
# Test Flask directly
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_segment":"Government","invoice_amount":100000,"customer_avg_past_delay":40}'

# Test via Express
curl -X POST http://localhost:5000/api/forecast \
  -H "Content-Type: application/json" \
  -d '{"customer_segment":"SMB","invoice_amount":45000,"customer_avg_past_delay":8.5}'
```

Expected response:

```json
{
  "predicted_days_late": 8.91,
  "risk_level": "MEDIUM"
}
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable        | Default                                          | Description            |
|-----------------|--------------------------------------------------|------------------------|
| `PORT`          | `5000`                                           | Express server port    |
| `MONGO_URI`     | `mongodb://localhost:27017/invoice-forecaster`   | MongoDB connection URI |
| `ML_SERVICE_URL`| `http://localhost:5001`                          | Flask service base URL |

---

## Screenshots

> _Add screenshots here once the UI is finalized._

| Dashboard — empty state | Dashboard — with predictions |
|------------------------|------------------------------|
| _(placeholder)_        | _(placeholder)_              |

---

## Future Improvements

### Data & Model
- [ ] **Real invoice data integration** — connect to QuickBooks, Xero, or SAP via API to replace synthetic training data with actual payment history.
- [ ] **Logistic regression for default-risk classification** — binary model predicting whether an invoice will default entirely (not just how late it pays).
- [ ] **Richer feature engineering** — add `invoice_age`, `days_until_due`, `outstanding_balance`, seasonality features.
- [ ] **Model retraining pipeline** — scheduled job that retrains on newly collected data and hot-swaps the pkl without restarting the service.
- [ ] **Confidence intervals** — return prediction uncertainty bands so operators know when a forecast is unreliable.

### Backend & Infrastructure
- [ ] **MongoDB persistence** — store submitted invoices and their predictions; power a historical audit trail.
- [ ] **Authentication & authorization** — JWT-based auth so each team sees only their own invoices.
- [ ] **Rate limiting & input sanitization** — harden the public-facing Express API.
- [ ] **Docker Compose** — single `docker-compose up` to start all three services.

### Frontend
- [ ] **Collections dashboard** — Kanban view: move invoices from *Pending* → *Contacted* → *Resolved*.
- [ ] **Analytics page** — bar charts of predicted delay by segment, risk distribution over time.
- [ ] **CSV import** — paste or upload a batch of invoices for bulk forecasting.
- [ ] **Export to PDF / Excel** — download the risk-sorted table for reporting.

---

## License

MIT
