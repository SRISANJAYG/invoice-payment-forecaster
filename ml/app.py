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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
