"""Generate a synthetic Nigerian bakery dataset (Mar to Aug 2026).

Usage:
    python generate_bakery_data.py --out . --seed 42

Outputs (in --out):
    products.csv           product master (starting price and unit cost, NGN)
    cost_changes.csv       dated unit cost changes (needs a point-in-time join)
    price_changes.csv      dated list price changes
    holidays.csv           public holidays (approximate dates)
    transactions_raw.csv   messy POS export, one row per line item
    production_log.csv     daily units produced and recorded waste
    ANSWER_KEY.md          ground truth and list of planted issues (open AFTER your analysis)
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

START, END = "2026-03-01", "2026-08-31"

# name, category, price, unit_cost, base_daily_demand, perishable, overbake_factor
PRODUCTS = [
    ("Agege Bread", "Bread", 1200, 780, 55, True, 1.08),
    ("Sliced Sandwich Bread", "Bread", 1800, 1150, 40, True, 1.08),
    ("Coconut Bread", "Bread", 1500, 950, 18, True, 1.70),
    ("Meat Pie", "Pastry", 1000, 620, 60, True, 1.10),
    ("Chicken Pie", "Pastry", 1200, 800, 35, True, 1.60),
    ("Sausage Roll", "Pastry", 700, 420, 45, True, 1.12),
    ("Doughnut", "Pastry", 500, 280, 40, True, 1.15),
    ("Egg Roll", "Pastry", 800, 450, 25, True, 1.15),
    ("Fish Roll", "Pastry", 600, 350, 30, True, 1.12),
    ("Puff Puff Pack", "Pastry", 500, 190, 30, True, 1.10),
    ("Chin Chin Pack", "Snack", 1000, 450, 20, False, 1.0),
    ("Birthday Cake 8in", "Cake", 25000, 16500, 1.5, False, 1.0),
    ("Cream Cake Slice", "Cake", 1800, 1950, 12, True, 1.30),
    ("Cupcake", "Cake", 800, 410, 25, True, 1.15),
    ("Banana Cake Loaf", "Cake", 3500, 2100, 6, True, 1.25),
    ("Red Velvet Slice", "Cake", 2000, 1250, 10, True, 1.25),
    ("Zobo Bottle", "Drink", 700, 380, 22, True, 1.10),
    ("Fresh Yoghurt Bottle", "Drink", 1500, 1250, 15, True, 1.20),
    ("Bottled Water", "Drink", 300, 200, 40, False, 1.0),
    ("Soft Drink", "Drink", 500, 400, 35, False, 1.0),
]

# Mon..Sun demand multipliers
WEEKDAY = {
    "Bread": [1.05, 1.0, 1.0, 1.0, 1.1, 1.15, 0.8],
    "Pastry": [0.95, 0.95, 1.0, 1.0, 1.15, 1.2, 0.9],
    "Snack": [0.9, 0.9, 0.95, 1.0, 1.1, 1.3, 1.1],
    "Cake": [0.7, 0.7, 0.8, 0.9, 1.2, 1.8, 1.5],
    "Drink": [0.9, 0.9, 1.0, 1.0, 1.1, 1.3, 1.2],
}
HOLIDAY_MULT = {"Bread": 0.85, "Pastry": 1.2, "Snack": 1.3, "Cake": 1.4, "Drink": 1.25}

HOURS = np.arange(7, 21)  # 07:00 to 20:59
HOUR_W = {
    "Bread": [10, 12, 9, 5, 4, 4, 4, 5, 7, 8, 7, 4, 2, 1],
    "Pastry": [4, 7, 9, 10, 10, 9, 7, 6, 6, 6, 5, 3, 2, 1],
    "Snack": [1, 2, 3, 5, 6, 7, 7, 7, 7, 7, 6, 4, 2, 1],
    "Cake": [1, 2, 4, 6, 8, 9, 9, 9, 9, 8, 7, 4, 2, 1],
    "Drink": [1, 3, 5, 7, 8, 9, 9, 9, 8, 7, 6, 4, 2, 1],
}

COST_CHANGES = [  # flour price shock on 2026-06-01, sugar/dairy shock on 2026-07-01
    ("Agege Bread", "2026-06-01", 1.18),
    ("Sliced Sandwich Bread", "2026-06-01", 1.18),
    ("Meat Pie", "2026-06-01", 1.15),
    ("Doughnut", "2026-06-01", 1.18),
    ("Chicken Pie", "2026-06-01", 1.12),
    ("Fresh Yoghurt Bottle", "2026-07-01", 1.10),
    ("Red Velvet Slice", "2026-07-01", 1.08),
]
PRICE_CHANGES = [
    ("Agege Bread", "2026-07-01", 1400),
    ("Sliced Sandwich Bread", "2026-07-15", 2000),
]

HOLIDAYS = {
    "2026-03-20": "Eid al-Fitr",
    "2026-04-03": "Good Friday",
    "2026-04-06": "Easter Monday",
    "2026-05-01": "Workers Day",
    "2026-05-27": "Eid al-Adha",
    "2026-06-12": "Democracy Day",
}


def build_histories():
    base = {p[0]: {"price": p[2], "cost": p[3]} for p in PRODUCTS}
    cost_hist = {}
    for name, d, mult in COST_CHANGES:
        cost_hist.setdefault(name, []).append((pd.Timestamp(d), round(base[name]["cost"] * mult)))
    price_hist = {}
    for name, d, price in PRICE_CHANGES:
        price_hist.setdefault(name, []).append((pd.Timestamp(d), price))
    return cost_hist, price_hist


def value_on(hist, name, d, default):
    val = default
    for eff, v in sorted(hist.get(name, [])):
        if d >= eff:
            val = v
    return val


def simulate(rng):
    dates = pd.date_range(START, END, freq="D")
    cost_hist, price_hist = build_histories()
    sales, prod, truth = [], [], []

    for d in dates:
        dow = d.dayofweek
        is_hol = d.strftime("%Y-%m-%d") in HOLIDAYS
        payday = 1.15 if d.day >= 25 else (1.05 if d.day <= 3 else 1.0)
        trend = 1 + 0.0004 * (d - dates[0]).days

        for name, cat, price0, cost0, base, perish, overbake in PRODUCTS:
            price = value_on(price_hist, name, d, price0)
            cost = value_on(cost_hist, name, d, cost0)
            elasticity = 0.9 if price > price0 else 1.0

            wf = WEEKDAY[cat][dow]
            hf = HOLIDAY_MULT[cat] if is_hol else 1.0
            lam = base * wf * hf * payday * trend * elasticity * rng.lognormal(0, 0.08)
            demand = int(rng.poisson(lam))

            if perish and name != "Birthday Cake 8in":
                planned = base * wf * overbake * rng.lognormal(0, 0.10)
                produced = int(round(planned))
            else:
                produced = demand  # made to order or non perishable
            sold = min(demand, produced)
            wasted = (produced - sold) if perish else 0

            remaining = sold
            revenue = 0.0
            while remaining > 0:
                q = int(rng.choice([1, 2, 3, 4], p=[0.60, 0.25, 0.10, 0.05]))
                if cat == "Cake" and name == "Birthday Cake 8in":
                    q = 1
                q = min(q, remaining)
                remaining -= q
                hour = int(rng.choice(HOURS, p=np.array(HOUR_W[cat]) / sum(HOUR_W[cat])))
                ts = d + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)),
                                      seconds=int(rng.integers(0, 60)))
                disc = 0
                if perish and hour >= 18 and rng.random() < 0.35:
                    disc = int(rng.choice([20, 30]))
                if name == "Fresh Yoghurt Bottle" and rng.random() < 0.20:
                    disc = max(disc, 30)
                if name == "Birthday Cake 8in" and rng.random() < 0.15:
                    disc = 10
                revenue += q * price * (1 - disc / 100)
                sales.append((ts, name, q, price, disc))

            prod.append((d, name, produced, wasted))
            truth.append((d, name, cat, sold, demand, produced, wasted, revenue,
                          sold * cost, wasted * cost))

    sales_df = pd.DataFrame(sales, columns=["ts", "product_name", "quantity", "unit_price",
                                            "discount_pct"])
    prod_df = pd.DataFrame(prod, columns=["date", "product_name", "units_produced",
                                          "units_wasted_true"])
    truth_df = pd.DataFrame(truth, columns=["date", "product_name", "category", "units_sold",
                                            "true_demand", "units_produced", "units_wasted",
                                            "revenue", "cogs_sold", "waste_cost"])
    return sales_df, prod_df, truth_df


def add_baskets(sales_df, rng):
    sales_df = sales_df.sort_values("ts").reset_index(drop=True)
    ids = np.empty(len(sales_df), dtype=object)
    counter = 0
    for _, idx in sales_df.groupby(sales_df["ts"].dt.date).groups.items():
        idx = list(idx)
        i = 0
        while i < len(idx):
            size = int(rng.choice([1, 2, 3, 4], p=[0.40, 0.30, 0.20, 0.10]))
            counter += 1
            for j in idx[i:i + size]:
                ids[j] = f"TX{counter:07d}"
            i += size
    sales_df["transaction_id"] = ids
    return sales_df


def make_messy(clean, rng):
    """Apply realistic data quality problems. Returns raw df and a dict of issue counts."""
    df = clean.copy()
    df["row_order"] = np.arange(len(df), dtype=float)
    issues = {}

    # Product name variants
    special = {"Sausage Roll": "Sausage Rol", "Chicken Pie": "Chiken Pie", "Doughnut": "Donut",
               "Sliced Sandwich Bread": "Sandwich Bread", "Fresh Yoghurt Bottle": "Yogurt Bottle"}
    fns = [str.lower, str.upper, lambda s: s + " ", lambda s: s.replace(" ", "  ")]
    mask = rng.random(len(df)) < 0.06
    names = df["product_name"].tolist()
    for i in np.where(mask)[0]:
        n = names[i]
        if n in special and rng.random() < 0.5:
            names[i] = special[n]
        else:
            names[i] = fns[int(rng.integers(0, len(fns)))](n)
    df["product_name"] = names
    issues["name_variants_rows"] = int(mask.sum())

    # Timestamp formats: one week exported as dd/mm/YYYY HH:MM
    ts_str = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    wk = (df["ts"] >= "2026-05-04") & (df["ts"] < "2026-05-11")
    ts_str[wk] = df.loc[wk, "ts"].dt.strftime("%d/%m/%Y %H:%M")
    df["timestamp"] = ts_str
    issues["ddmmyyyy_rows"] = int(wk.sum())

    # Missing unit price, outlier quantity, missing discount
    m = rng.random(len(df)) < 0.004
    df.loc[m, "unit_price"] = np.nan
    issues["missing_unit_price_rows"] = int(m.sum())
    m = rng.random(len(df)) < 0.0005
    df.loc[m, "quantity"] = df.loc[m, "quantity"] * 10
    issues["quantity_x10_outlier_rows"] = int(m.sum())
    df["discount_pct"] = df["discount_pct"].astype(float)
    m = (df["discount_pct"] == 0) & (rng.random(len(df)) < 0.05)
    df.loc[m, "discount_pct"] = np.nan
    issues["blank_discount_rows"] = int(m.sum())

    # Payment method and cashier
    pay = rng.choice(["Cash", "cash", "Transfer", "transfer", "TRANSFER", "POS", "pos", "Pos"],
                     size=len(df), p=[.22, .10, .20, .10, .05, .20, .08, .05])
    df["payment_method"] = pay
    df["cashier"] = rng.choice(["Ada", "Bisi", "Chidi", "Femi"], size=len(df))
    df.loc[rng.random(len(df)) < 0.03, "cashier"] = np.nan

    extra = []
    # Exact duplicate rows (double export)
    dup = df[rng.random(len(df)) < 0.008].copy()
    dup["row_order"] += 0.1
    extra.append(dup)
    issues["exact_duplicate_rows"] = len(dup)
    # Refunds (negative quantity, later time)
    ref = df[rng.random(len(df)) < 0.004].copy()
    ref["quantity"] = -ref["quantity"].abs()
    ref["row_order"] += 0.5
    extra.append(ref)
    issues["refund_rows_negative_qty"] = len(ref)
    # Test transactions
    n_test = 12
    pos = rng.integers(0, len(df), n_test)
    test = pd.DataFrame({
        "transaction_id": [f"TEST{i:03d}" for i in range(n_test)],
        "timestamp": df["timestamp"].to_numpy()[pos],
        "product_name": "TEST ITEM", "quantity": 1, "unit_price": 1.0, "discount_pct": 0.0,
        "payment_method": "Cash", "cashier": "Ada", "row_order": pos + 0.7})
    extra.append(test)
    issues["test_rows"] = n_test

    raw = pd.concat([df] + extra, ignore_index=True).sort_values("row_order", kind="stable")
    cols = ["transaction_id", "timestamp", "product_name", "quantity", "unit_price",
            "discount_pct", "payment_method", "cashier"]
    return raw[cols].reset_index(drop=True), issues


def main(out, seed):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    sales_df, prod_df, truth_df = simulate(rng)
    sales_df = add_baskets(sales_df, rng)
    raw, issues = make_messy(sales_df, rng)

    # Production log: recorded waste is missing on about 12 percent of perishable rows
    perish = {p[0] for p in PRODUCTS if p[5]}
    plog = prod_df.copy()
    plog["units_wasted_recorded"] = plog["units_wasted_true"].astype(float)
    miss = plog["product_name"].isin(perish) & (rng.random(len(plog)) < 0.12)
    plog.loc[miss, "units_wasted_recorded"] = np.nan
    issues["missing_recorded_waste_rows"] = int(miss.sum())
    plog = plog.drop(columns="units_wasted_true")
    plog["date"] = plog["date"].dt.strftime("%Y-%m-%d")

    products = pd.DataFrame(
        [(p[0], p[1], p[2], p[3], p[5]) for p in PRODUCTS],
        columns=["product_name", "category", "list_price_start", "unit_cost_start",
                 "is_perishable"])
    cost_changes = pd.DataFrame(COST_CHANGES, columns=["product_name", "effective_date",
                                                       "multiplier"])
    base_cost = products.set_index("product_name")["unit_cost_start"]
    cost_changes["new_unit_cost"] = [round(base_cost[n] * m) for n, _, m in COST_CHANGES]
    cost_changes = cost_changes.drop(columns="multiplier")
    price_changes = pd.DataFrame(PRICE_CHANGES, columns=["product_name", "effective_date",
                                                         "new_list_price"])
    holidays = pd.DataFrame(sorted(HOLIDAYS.items()), columns=["date", "holiday"])

    products.to_csv(out / "products.csv", index=False)
    cost_changes.to_csv(out / "cost_changes.csv", index=False)
    price_changes.to_csv(out / "price_changes.csv", index=False)
    holidays.to_csv(out / "holidays.csv", index=False)
    raw.to_csv(out / "transactions_raw.csv", index=False)
    plog.to_csv(out / "production_log.csv", index=False)

    write_answer_key(out, truth_df, issues, len(raw))
    print(f"transactions_raw rows: {len(raw):,}")
    print(f"files written to: {out.resolve()}")


def write_answer_key(out, t, issues, n_raw):
    g = t.groupby("product_name").agg(
        revenue=("revenue", "sum"), cogs_sold=("cogs_sold", "sum"),
        waste_cost=("waste_cost", "sum"), units_sold=("units_sold", "sum"),
        units_wasted=("units_wasted", "sum"), true_demand=("true_demand", "sum"))
    g["gross_profit_sold_only"] = g["revenue"] - g["cogs_sold"]
    g["profit_after_waste"] = g["gross_profit_sold_only"] - g["waste_cost"]
    g["margin_after_waste_pct"] = 100 * g["profit_after_waste"] / g["revenue"]
    g["lost_sales_units"] = g["true_demand"] - g["units_sold"]
    g = g.sort_values("profit_after_waste", ascending=False).round(1)

    losers = g[g["profit_after_waste"] < 0]
    only_after_waste = g[(g["gross_profit_sold_only"] > 0) & (g["profit_after_waste"] < 0)]

    lines = [
        "# ANSWER KEY (open after you finish your own analysis)",
        "",
        "All amounts in NGN. Ground truth comes from the simulator before dirtying.",
        "",
        "## Planted data quality issues (raw file rows: %s)" % f"{n_raw:,}",
    ]
    lines += [f"- {k}: {v}" for k, v in issues.items()]
    lines += [
        "- product names have case, spacing and spelling variants (for example Donut, Chiken Pie)",
        "- discount_pct blank can mean 0 or missing; clean POS data does not tell you which",
        "- 2026-05-04 to 2026-05-10 timestamps are dd/mm/YYYY, all other rows are ISO",
        "",
        "## Planted business traps",
        "- Cream Cake Slice is priced below its unit cost (loss on every sale).",
        "- Some items look profitable on sold units but lose money once waste is counted.",
        "- Unit costs rose on 2026-06-01 and 2026-07-01, so a single static cost is wrong.",
        "- Agege Bread and Sandwich Bread list prices rose mid period (demand dipped about 10 percent).",
        "- Fresh Yoghurt Bottle has heavy 30 percent promos.",
        "- Sales equal min(demand, units produced), so sales are censored demand. Stockouts hide demand.",
        "- Weekend and payday (day 25 onward) effects, plus holiday lifts, exist for forecasting.",
        "",
        "## True product profitability over the full period",
        "",
        g[["revenue", "cogs_sold", "waste_cost", "profit_after_waste",
           "margin_after_waste_pct", "units_wasted", "lost_sales_units"]].to_markdown(floatfmt=",.1f"),
        "",
        "Loss-making after waste: " + ", ".join(losers.index),
        "Profitable on sold units only, but loss-making after waste: "
        + (", ".join(only_after_waste.index) or "none"),
    ]
    (out / "ANSWER_KEY.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    main(args.out, args.seed)
