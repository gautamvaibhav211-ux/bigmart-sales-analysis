# Data Files

## Source

`raw/bigmart_sales_raw.csv` is the 8,523-row BigMart Sales training file (12 columns, 2013 sales for 1,559 products across 10 outlets).

- Original release: Analytics Vidhya practice problem, [Big Mart Sales III](https://datahack.analyticsvidhya.com/contest/practice-problem-big-mart-sales-iii/)
- Copy used: [BigMart Sales Dataset on Kaggle](https://www.kaggle.com/datasets/yasserh/bigmartsalesdataset) by Yasser H

The raw file is unchanged and is the input to `../python/01_data_cleaning.py`.

## Derived data

`cleaned/bigmart_sales_cleaned.csv` is created by the cleaning script. It is not a separate source dataset. It standardises labels, fills missing values, replaces zero visibility values and adds 5 derived columns (`Outlet_Age`, `Item_Category`, `Price_Per_Unit_Weight`, `MRP_Tier`, `Outlet_Size_Imputed`).

`Outlet_Size_Imputed = Yes` marks the 2,410 records (3 whole outlets) where the size was missing in the raw data and was filled in with an assumption.

