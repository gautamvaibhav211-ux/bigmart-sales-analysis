"""Create the exploratory charts from the cleaned BigMart data.

Input : data/cleaned/bigmart_sales_cleaned.csv  (run 01_data_cleaning.py first)
Output: PNG charts in images/

Source: BigMart Sales dataset (Analytics Vidhya / Kaggle, Yasser H). See the README.
All charts describe associations in this dataset; none of them show cause and effect.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "data" / "cleaned" / "bigmart_sales_cleaned.csv"
IMAGE_DIR = ROOT / "images"
IMAGE_DIR.mkdir(exist_ok=True)

df = pd.read_csv(CLEAN_PATH)
SALES = "Item_Outlet_Sales"


def save_bar(labels, values, title, xlabel, ylabel, filename, rotation=0, horizontal=False):
    fig, ax = plt.subplots(figsize=(9, 5))
    if horizontal:
        ax.barh(labels[::-1], values[::-1])
        ax.grid(axis="x", alpha=0.25)
    else:
        ax.bar(labels, values)
        ax.grid(axis="y", alpha=0.25)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=rotation)
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / filename, dpi=180)
    plt.close(fig)


# 1. Total sales by outlet type
by_type = df.groupby("Outlet_Type")[SALES].sum().sort_values(ascending=False)
save_bar(by_type.index.tolist(), by_type.values.tolist(), "Sales by Outlet Type",
         "Outlet type", "Total sales (₹)", "01_sales_by_outlet_type.png", rotation=15)

# 2. Total sales by individual outlet
by_outlet = df.groupby("Outlet_Identifier")[SALES].sum().sort_values(ascending=False)
save_bar(by_outlet.index.tolist(), by_outlet.values.tolist(), "Sales by Individual Outlet",
         "Outlet", "Total sales (₹)", "02_sales_by_outlet.png", rotation=45)

# 3. Average sales per record by city tier
by_tier = df.groupby("Outlet_Location_Type")[SALES].mean()
save_bar(by_tier.index.tolist(), by_tier.values.tolist(), "Average Sales per Record by City Tier",
         "City tier", "Average sales (₹)", "03_avg_sales_by_tier.png")

# 4. Sales share by item category
by_category = df.groupby("Item_Category")[SALES].sum()
fig, ax = plt.subplots(figsize=(7, 5))
ax.pie(by_category, labels=by_category.index, autopct="%1.1f%%")
ax.set_title("Sales Share by Item Category")
fig.tight_layout()
fig.savefig(IMAGE_DIR / "04_sales_by_category.png", dpi=180)
plt.close(fig)

# 5. Top 10 item types by total sales
top_types = df.groupby("Item_Type")[SALES].sum().sort_values(ascending=False).head(10)
save_bar(top_types.index.tolist(), top_types.values.tolist(), "Top 10 Item Types by Sales",
         "Item type", "Total sales (₹)", "05_top_item_types.png", horizontal=True)

# 6. MRP vs sales (3,500-point sample for readability; trend line uses all rows)
sample = df.sample(min(3500, len(df)), random_state=42)
slope, intercept = np.polyfit(df["Item_MRP"], df[SALES], 1)
x_line = np.linspace(df["Item_MRP"].min(), df["Item_MRP"].max(), 100)
r_mrp = df["Item_MRP"].corr(df[SALES])
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(sample["Item_MRP"], sample[SALES], alpha=0.28, s=14)
ax.plot(x_line, slope * x_line + intercept, linewidth=2, label=f"Linear trend (r={r_mrp:.2f})")
ax.set_title("MRP vs Outlet Sales — Association")
ax.set_xlabel("MRP (₹)")
ax.set_ylabel("Sales (₹)")
ax.legend()
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(IMAGE_DIR / "06_mrp_vs_sales.png", dpi=180)
plt.close(fig)

# 7. Average sales by outlet establishment year
by_year = df.groupby("Outlet_Establishment_Year")[SALES].mean()
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(by_year.index, by_year.values, marker="o")
ax.set_title("Average Sales by Outlet Establishment Year")
ax.set_xlabel("Establishment year")
ax.set_ylabel("Average sales (₹)")
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig(IMAGE_DIR / "07_sales_by_establishment_year.png", dpi=180)
plt.close(fig)

# 8. Average sales by shelf-visibility bucket
bucket_labels = ["Low (<5%)", "Medium (5-10%)", "High (10-15%)", "Very High (15%+)"]
bucket = pd.cut(df["Item_Visibility"], [0, 0.05, 0.10, 0.15, 1], labels=bucket_labels, include_lowest=True)
by_bucket = df.assign(bucket=bucket).groupby("bucket", observed=True)[SALES].mean()
save_bar(by_bucket.index.astype(str).tolist(), by_bucket.values.tolist(),
         "Average Sales by Visibility Bucket", "Visibility bucket", "Average sales (₹)",
         "08_sales_by_visibility.png", rotation=15)

print(f"Total sales: ₹{df[SALES].sum():,.0f}")
print(f"MRP-sales correlation: {r_mrp:.2f}")
print(f"Visibility-sales correlation: {df['Item_Visibility'].corr(df[SALES]):.2f}")
print(f"Outlet age-sales correlation: {df['Outlet_Age'].corr(df[SALES]):.2f}")
