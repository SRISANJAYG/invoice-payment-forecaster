"""
generate_data.py
Generates a synthetic invoices.csv dataset for the Invoice Forecaster project.
Run once: python generate_data.py
"""

import random
import csv
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(42)

SEGMENTS = ["Enterprise", "SMB", "Startup", "Government"]
TERMS = [15, 30, 45, 60]

# Rough per-segment base delay distributions (mean, std)
SEGMENT_DELAY = {
    "Enterprise":  (5,  8),
    "SMB":         (12, 15),
    "Startup":     (20, 18),
    "Government":  (30, 20),
}

NUM_RECORDS = 1000

# Build a small customer pool so avg_past_delay is realistic
customer_pool = {}
for _ in range(200):
    cid = fake.uuid4()[:8]
    seg = random.choice(SEGMENTS)
    mean, std = SEGMENT_DELAY[seg]
    avg = max(0, random.gauss(mean, std))
    customer_pool[cid] = {"segment": seg, "avg_past_delay": round(avg, 1)}

customers = list(customer_pool.keys())

rows = []
for i in range(1, NUM_RECORDS + 1):
    cid = random.choice(customers)
    seg = customer_pool[cid]["segment"]
    avg_past = customer_pool[cid]["avg_past_delay"]

    amount = round(random.uniform(500, 50_000), 2)
    inv_date = fake.date_between(start_date="-2y", end_date="-30d")
    terms = random.choice(TERMS)
    due_date = inv_date + timedelta(days=terms)

    mean, std = SEGMENT_DELAY[seg]
    # days_late influenced by segment baseline + customer history + amount noise
    noise = random.gauss(0, 5)
    days_late = max(
        0,
        round(0.4 * mean + 0.4 * avg_past + 0.001 * (amount / 1000) * 10 + noise),
    )

    base_delay = round(random.gauss(mean, std / 2))
    amount_penalty = round(amount * 0.015 * (days_late / 30), 2)

    rows.append(
        {
            "invoice_id": f"INV-{i:05d}",
            "customer_id": cid,
            "invoice_amount": amount,
            "invoice_date": inv_date.isoformat(),
            "customer_segment": seg,
            "terms": terms,
            "due_date": due_date.isoformat(),
            "base_delay": base_delay,
            "amount_penalty": amount_penalty,
            "days_late": days_late,
            "customer_avg_past_delay": avg_past,
        }
    )

fieldnames = [
    "invoice_id", "customer_id", "invoice_amount", "invoice_date",
    "customer_segment", "terms", "due_date", "base_delay",
    "amount_penalty", "days_late", "customer_avg_past_delay",
]

with open("invoices.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] Generated invoices.csv with {NUM_RECORDS} records.")
