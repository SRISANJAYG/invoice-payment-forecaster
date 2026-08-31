"""
generate_sample_batch.py
Generates a 50-row sample_batch.csv for demo/testing the /predict-batch endpoint.
Includes actual_days_late as ground truth so match_rate can be computed.

Run: python generate_sample_batch.py
"""

import random
import csv
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(99)  # different seed from generate_data.py so it's a fresh sample

SEGMENTS = ["Enterprise", "SMB", "Startup", "Government"]
TERMS    = [15, 30, 45, 60]

SEGMENT_DELAY = {
    "Enterprise":  (5,  8),
    "SMB":         (12, 15),
    "Startup":     (20, 18),
    "Government":  (30, 20),
}

NUM_RECORDS = 50

# Small customer pool for realistic avg_past_delay values
customer_pool = {}
for _ in range(40):
    cid = fake.uuid4()[:8]
    seg = random.choice(SEGMENTS)
    mean, std = SEGMENT_DELAY[seg]
    # Intentionally include some zero-history customers for the unresolved demo
    avg = 0.0 if random.random() < 0.15 else max(0, random.gauss(mean, std))
    customer_pool[cid] = {"segment": seg, "avg_past_delay": round(avg, 1)}

customers = list(customer_pool.keys())

rows = []
for i in range(1, NUM_RECORDS + 1):
    cid = random.choice(customers)
    seg = customer_pool[cid]["segment"]
    avg_past = customer_pool[cid]["avg_past_delay"]

    amount   = round(random.uniform(1_000, 150_000), 2)
    inv_date = fake.date_between(start_date="-1y", end_date="-30d")
    terms    = random.choice(TERMS)
    due_date = inv_date + timedelta(days=terms)

    mean, std = SEGMENT_DELAY[seg]
    noise = random.gauss(0, 4)
    actual_days_late = max(
        0,
        round(0.4 * mean + 0.4 * avg_past + 0.001 * (amount / 1000) * 10 + noise),
    )

    rows.append({
        "customer_segment":        seg,
        "invoice_amount":          amount,
        "invoice_date":            inv_date.isoformat(),
        "due_date":                due_date.isoformat(),
        "terms":                   terms,
        "customer_avg_past_delay": avg_past,
        "actual_days_late":        actual_days_late,
    })

fieldnames = [
    "customer_segment", "invoice_amount", "invoice_date",
    "due_date", "terms", "customer_avg_past_delay", "actual_days_late",
]

with open("sample_batch.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] Generated sample_batch.csv with {NUM_RECORDS} records.")
