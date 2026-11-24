"""Clean the BigMart Sales dataset.

Input : data/raw/bigmart_sales_raw.csv     (8,523 item-outlet records, 12 columns)
Output: data/cleaned/bigmart_sales_cleaned.csv

Source: BigMart Sales dataset (Analytics Vidhya "Big Mart Sales III" practice problem),
as shared on Kaggle by Yasser H:
https://www.kaggle.com/datasets/yasserh/bigmartsalesdataset
See the repository README for dataset attribution.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "bigmart_sales_raw.csv"
CLEAN_PATH = ROOT / "data" / "cleaned" / "bigmart_sales_cleaned.csv"

DATA_YEAR = 2013  # the dataset holds 2013 sales, so outlet age is measured in 2013
CATEGORY_BY_PREFIX = {"FD": "Food", "DR": "Drinks", "NC": "Non-Consumable"}
OUTPUT_COLUMNS = [
    "Item_Identifier", "Item_Weight", "Item_Fat_Content", "Item_Visibility", "Item_Type", "Item_MRP",
    "Outlet_Identifier", "Outlet_Establishment_Year", "Outlet_Size", "Outlet_Location_Type",
    "Outlet_Type", "Item_Outlet_Sales",
    "Outlet_Age", "Item_Category", "Price_Per_Unit_Weight", "MRP_Tier", "Outlet_Size_Imputed",
]
FAT_LABELS = {"LF": "Low Fat", "low fat": "Low Fat", "Low Fat": "Low Fat",
              "reg": "Regular", "Regular": "Regular"}


def standardise_fat_content(df):
    """Fix inconsistent labels; non-consumables cannot be 'Low Fat', so label them 'Non-Edible'."""
    df["Item_Fat_Content"] = df["Item_Fat_Content"].replace(FAT_LABELS)
    df.loc[df["Item_Category"] == "Non-Consumable", "Item_Fat_Content"] = "Non-Edible"
    return df


def impute_item_weight(df):
    """Missing weight -> same product's mean weight in other outlets, then item-type median, then overall median."""
    product_mean = df.groupby("Item_Identifier")["Item_Weight"].transform("mean")
    type_median = df.groupby("Item_Type")["Item_Weight"].transform("median")
    df["Item_Weight"] = (df["Item_Weight"]
                         .fillna(product_mean)
                         .fillna(type_median)
                         .fillna(df["Item_Weight"].median()))
    return df


def impute_outlet_size(df):
    """Missing size -> most common size among outlets of the same type.

    Three whole outlets (OUT010, OUT017, OUT045) have no size at all, so this is an
    assumption, not recovered data. The Outlet_Size_Imputed flag keeps it visible.
    """
    df["Outlet_Size_Imputed"] = np.where(df["Outlet_Size"].isna(), "Yes", "No")
    known = df.dropna(subset=["Outlet_Size"])
    mode_by_type = known.groupby("Outlet_Type")["Outlet_Size"].agg(lambda s: s.mode().iat[0])
    overall_mode = known["Outlet_Size"].mode().iat[0]
    fill = df["Outlet_Type"].map(mode_by_type).fillna(overall_mode)
    df["Outlet_Size"] = df["Outlet_Size"].fillna(fill)
    return df


def impute_item_visibility(df):
    """A visibility of exactly 0 is not realistic for a stocked item, so treat it as missing.

    Replace with the same product's mean non-zero visibility, then the item-type median,
    then the overall median.
    """
    nonzero = df[df["Item_Visibility"] > 0]
    product_mean = nonzero.groupby("Item_Identifier")["Item_Visibility"].mean()
    type_median = nonzero.groupby("Item_Type")["Item_Visibility"].median()
    is_zero = df["Item_Visibility"].eq(0)
    replacement = (df.loc[is_zero, "Item_Identifier"].map(product_mean)
                   .fillna(df.loc[is_zero, "Item_Type"].map(type_median))
                   .fillna(nonzero["Item_Visibility"].median()))
    df.loc[is_zero, "Item_Visibility"] = replacement
    return df


def add_features(df):
    df["Outlet_Age"] = DATA_YEAR - df["Outlet_Establishment_Year"]
    df["Price_Per_Unit_Weight"] = (df["Item_MRP"] / df["Item_Weight"]).round(2)
    df["MRP_Tier"] = pd.cut(df["Item_MRP"], [0, 70, 140, 210, np.inf],
                            labels=["Low", "Medium", "High", "Premium"], include_lowest=True)
    return df


def validate(df, raw_rows):
    """Stop the script if the cleaned data breaks any expectation."""
    assert len(df) == raw_rows == 8523, f"Row count changed: {raw_rows} -> {len(df)}"
    assert df.isna().sum().sum() == 0, "Missing values remain after cleaning"
    assert (df["Item_Visibility"] > 0).all(), "Zero visibility values remain"
    assert set(df["Item_Fat_Content"]) == {"Low Fat", "Regular", "Non-Edible"}, "Unexpected fat labels"
    assert not df.duplicated(["Item_Identifier", "Outlet_Identifier"]).any(), "Item-outlet pair repeats"
    assert df["Item_Category"].isin(CATEGORY_BY_PREFIX.values()).all(), "Unknown item category"
    assert (df["Item_Outlet_Sales"] > 0).all(), "Non-positive sales value"


def main():
    df = pd.read_csv(RAW_PATH)
    df.columns = df.columns.str.strip()
    raw_rows = len(df)

    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()
    missing_weight = int(df["Item_Weight"].isna().sum())
    missing_size = int(df["Outlet_Size"].isna().sum())
    zero_visibility = int((df["Item_Visibility"] == 0).sum())

    df["Item_Category"] = df["Item_Identifier"].str[:2].map(CATEGORY_BY_PREFIX).fillna("Other")
    df = standardise_fat_content(df)
    df = impute_item_weight(df)
    df = impute_outlet_size(df)
    df = impute_item_visibility(df)
    df = add_features(df)

    df = df[OUTPUT_COLUMNS]
    validate(df, raw_rows)

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)

    print(f"Raw rows: {raw_rows:,} | duplicate rows removed: {duplicates:,} | final rows: {len(df):,}")
    print(f"Missing weight fixed: {missing_weight:,} | missing outlet size filled: {missing_size:,} "
          f"| zero visibility fixed: {zero_visibility:,}")
    print("All validation checks passed.")


if __name__ == "__main__":
    main()
