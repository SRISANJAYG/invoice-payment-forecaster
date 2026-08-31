"""
app.py  –  Invoice Forecaster ML microservice
Endpoints:
  GET  /health   – liveness check
  POST /predict  – returns predicted_days_late, risk_level, and reason
"""

import os
import pickle

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)  # allow all origins; restrict in production

MODEL_PATH = os.path.join(os.path.dirname(__file__), "forecast_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

REQUIRED_FIELDS = {"customer_segment", "invoice_amount", "customer_avg_past_delay"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def risk_level(days: float) -> str:
    if days > 10:
        return "HIGH"
    if days >= 3:
        return "MEDIUM"
    return "LOW"


def build_reason(segment: str, amount: float, avg_delay: float, level: str) -> str:
    """Compose a short human-readable explanation of the key prediction drivers."""
    factors = []

    if avg_delay == 0:
        factors.append("no payment history — using segment average")
    elif avg_delay > 15:
        factors.append("a history of significant delays")

    if amount > 100_000:
        factors.append("a large invoice amount")

    if not factors:
        # Fallback: explain purely from the segment baseline
        return (
            f"Flagged {level}: prediction is based on the {segment} segment baseline."
        )

    joined = " and ".join(factors)
    return f"Flagged {level}: customer has {joined}."


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"status": "ok", "message": "ML service is running"})


@app.post("/predict")
def predict():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    missing = REQUIRED_FIELDS - body.keys()
    if missing:
        return jsonify({"error": f"Missing fields: {sorted(missing)}"}), 400

    try:
        invoice_amount = float(body["invoice_amount"])
        customer_avg_past_delay = float(body["customer_avg_past_delay"])
        customer_segment = str(body["customer_segment"])
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid field value: {exc}"}), 400

    df = pd.DataFrame(
        [
            {
                "customer_segment": customer_segment,
                "invoice_amount": invoice_amount,
                "customer_avg_past_delay": customer_avg_past_delay,
            }
        ]
    )

    raw_pred = model.predict(df)[0]
    days = min(90.0, max(0.0, float(raw_pred)))
    level = risk_level(days)
    reason = build_reason(customer_segment, invoice_amount, customer_avg_past_delay, level)

    return jsonify(
        {
            "predicted_days_late": round(days, 2),
            "risk_level": level,
            "reason": reason,
        }
    )


@app.post("/predict-batch")
def predict_batch():
    body = request.get_json(silent=True)
    if not body or not isinstance(body, list):
        return jsonify({"error": "Request body must be a JSON array of invoice objects"}), 400
    if len(body) == 0:
        return jsonify({"error": "Batch must contain at least one invoice"}), 400
    if len(body) > 500:
        return jsonify({"error": "Batch size cannot exceed 500 invoices"}), 400

    results = []
    high_risk_count = 0
    unresolved_count = 0
    accurate_count = 0
    actuals_provided = 0

    for idx, inv in enumerate(body):
        missing = REQUIRED_FIELDS - inv.keys()
        if missing:
            results.append({"index": idx, "error": f"Missing fields: {sorted(missing)}"})
            continue

        try:
            invoice_amount        = float(inv["invoice_amount"])
            customer_avg_past_delay = float(inv["customer_avg_past_delay"])
            customer_segment      = str(inv["customer_segment"])
        except (ValueError, TypeError) as exc:
            results.append({"index": idx, "error": f"Invalid field value: {exc}"})
            continue

        df = pd.DataFrame([{
            "customer_segment":        customer_segment,
            "invoice_amount":          invoice_amount,
            "customer_avg_past_delay": customer_avg_past_delay,
        }])

        raw_pred = model.predict(df)[0]
        days  = min(90.0, max(0.0, float(raw_pred)))
        level = risk_level(days)
        reason = build_reason(customer_segment, invoice_amount, customer_avg_past_delay, level)

        is_unresolved = customer_avg_past_delay == 0
        if is_unresolved:
            unresolved_count += 1
        if level == "HIGH":
            high_risk_count += 1

        row = {
            "index":                  idx,
            "customer_segment":       customer_segment,
            "invoice_amount":         invoice_amount,
            "customer_avg_past_delay": customer_avg_past_delay,
            "predicted_days_late":    round(days, 2),
            "risk_level":             level,
            "reason":                 reason,
            "is_unresolved":          is_unresolved,
        }

        # Ground truth — optional
        actual_raw = inv.get("actual_days_late")
        if actual_raw is not None and actual_raw != "":
            try:
                actual = float(actual_raw)
                is_accurate = abs(days - actual) <= 5
                row["actual_days_late"] = actual
                row["accurate"] = is_accurate
                if is_accurate:
                    accurate_count += 1
                actuals_provided += 1
            except (ValueError, TypeError):
                pass  # ignore unparseable actuals

        results.append(row)

    match_rate_percent = (
        round((accurate_count / actuals_provided) * 100, 1)
        if actuals_provided > 0 else None
    )

    return jsonify({
        "total_processed":    len(results),
        "high_risk_count":    high_risk_count,
        "match_rate_percent": match_rate_percent,
        "unresolved_count":   unresolved_count,
        "results":            results,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)

