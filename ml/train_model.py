"""
train_model.py
Trains a Linear Regression model to predict days_late for an invoice.

Features : customer_segment (OneHotEncoded), invoice_amount, customer_avg_past_delay
Target   : days_late
Split    : 80 / 20 train / test
Output   : MAE, RMSE printed to console; model saved as forecast_model.pkl
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("invoices.csv")
print(f"Loaded {len(df)} rows from invoices.csv")
print(df[["customer_segment", "invoice_amount", "customer_avg_past_delay", "days_late"]].head())

# ── 2. Define features & target ───────────────────────────────────────────────
CATEGORICAL = ["customer_segment"]
NUMERICAL   = ["invoice_amount", "customer_avg_past_delay"]

X = df[CATEGORICAL + NUMERICAL]
y = df["days_late"]

# ── 3. Train / test split (80 / 20) ──────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"\nTrain size: {len(X_train)}  |  Test size: {len(X_test)}")

# ── 4. Build pipeline (OneHotEncoder + LinearRegression) ─────────────────────
preprocessor = ColumnTransformer(
    transformers=[
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ("num", "passthrough", NUMERICAL),
    ]
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression()),
    ]
)

# ── 5. Train ──────────────────────────────────────────────────────────────────
pipeline.fit(X_train, y_train)
print("\nModel trained [OK]")

# ── 6. Evaluate ───────────────────────────────────────────────────────────────
y_pred = pipeline.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = root_mean_squared_error(y_test, y_pred)

print(f"\n-- Evaluation on test set ------------------")
print(f"   MAE  : {mae:.4f} days")
print(f"   RMSE : {rmse:.4f} days")
print(f"--------------------------------------------")

# -- 7. Save model ------------------------------------------------------------
MODEL_PATH = "forecast_model.pkl"
with open(MODEL_PATH, "wb") as f:
    pickle.dump(pipeline, f)

print(f"\nModel saved -> {MODEL_PATH}")
