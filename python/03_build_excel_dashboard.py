"""Build excel/BigMart_Sales_Dashboard.xlsx from the cleaned data.

Input : data/cleaned/bigmart_sales_cleaned.csv  (run 01_data_cleaning.py first)
Output: excel/BigMart_Sales_Dashboard.xlsx

Every number on the Summary and Dashboard sheets is an Excel formula (SUMIFS, COUNTIFS,
AVERAGEIFS) over the Data sheet. Only the row labels, such as outlet names and bucket
limits, are typed in, and the "Top Item Types" order is fixed when the file is built.
After building, open the file in Excel (or run LibreOffice recalculation) so the
formulas have saved results, which keeps previews and charts from showing blanks.

Source: BigMart Sales dataset (Analytics Vidhya / Kaggle, Yasser H). See the README.
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "data" / "cleaned" / "bigmart_sales_cleaned.csv"
OUT_PATH = ROOT / "excel" / "BigMart_Sales_Dashboard.xlsx"

df = pd.read_csv(CLEAN_PATH)
N = len(df)
LAST = N + 1  # last data row on the Data sheet (row 1 is the header)

# Data sheet column letters, looked up by name so the formulas stay readable
COL = {name: get_column_letter(i + 1) for i, name in enumerate(df.columns)}


def rng(name):
    return f"Data!${COL[name]}$2:${COL[name]}${LAST}"


SALES, OUTLET_TYPE, OUTLET_ID = rng("Item_Outlet_Sales"), rng("Outlet_Type"), rng("Outlet_Identifier")
CATEGORY, TIER, ITEM_TYPE = rng("Item_Category"), rng("Outlet_Location_Type"), rng("Item_Type")
MRP, MRP_TIER, VIS, YEAR = rng("Item_MRP"), rng("MRP_Tier"), rng("Item_Visibility"), rng("Outlet_Establishment_Year")

NAVY = "17324D"
FONT = "Arial"
title_font = Font(name=FONT, size=16, bold=True, color="FFFFFF")
head_font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
body_font = Font(name=FONT, size=10)
bold_font = Font(name=FONT, size=10, bold=True)
note_font = Font(name=FONT, size=9, italic=True, color="595959")
navy_fill = PatternFill("solid", fgColor=NAVY)
light_fill = PatternFill("solid", fgColor="E9EEF4")
thin = Side(style="thin", color="BFBFBF")
box = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
dash = wb.active
dash.title = "Dashboard"
summ = wb.create_sheet("Summary")
data = wb.create_sheet("Data")
quality = wb.create_sheet("Data Quality")

# ------------------------------------------------------------------ Data sheet
data.append(list(df.columns))
for row in df.itertuples(index=False):
    data.append(list(row))
for cell in data[1]:
    cell.font, cell.fill = head_font, navy_fill
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for i, name in enumerate(df.columns, start=1):
    data.column_dimensions[get_column_letter(i)].width = max(14, min(26, len(name) + 4))
data.freeze_panes = "A2"
data.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{LAST}"

# --------------------------------------------------------------- Summary sheet
summ["A1"] = "Big Mart Sales — Analysis Summary"
summ["A1"].font = Font(name=FONT, size=14, bold=True)
summ["A2"] = ("All numbers are formulas over the Data sheet. Sales are recorded 2013 sales in this public "
              "dataset (item-outlet records), not profit.")
summ["A2"].font = note_font

positions = {}  # table name -> (first data row, last data row)
cursor = 4


def table(name, title, headers, labels, formulas, formats, note=None):
    """Write a titled table. `formulas` are templates using {r} (row) and {label} (cell holding the label)."""
    global cursor
    summ.cell(row=cursor, column=1, value=title).font = Font(name=FONT, size=11, bold=True, color=NAVY)
    cursor += 1
    for j, h in enumerate(headers, start=1):
        c = summ.cell(row=cursor, column=j, value=h)
        c.font, c.fill, c.border = head_font, navy_fill, box
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    first = cursor + 1
    for k, label in enumerate(labels):
        r = first + k
        c = summ.cell(row=r, column=1, value=label)
        c.font, c.border = body_font, box
        for j, (tmpl, fmt) in enumerate(zip(formulas, formats), start=2):
            cell = summ.cell(row=r, column=j, value=tmpl.format(r=r, first=first, last=first + len(labels) - 1))
            cell.font, cell.border, cell.number_format = body_font, box, fmt
    last = first + len(labels) - 1
    positions[name] = (first, last)
    cursor = last + 1
    if note:
        summ.cell(row=cursor, column=1, value=note).font = note_font
        cursor += 1
    cursor += 1


by = lambda col: df.groupby(col)["Item_Outlet_Sales"].sum().sort_values(ascending=False).index.tolist()

table("type", "Outlet Type Performance", ["Outlet Type", "Total Sales", "Records", "Avg Sales per Record"],
      by("Outlet_Type"),
      [f"=SUMIFS({SALES},{OUTLET_TYPE},$A{{r}})", f"=COUNTIFS({OUTLET_TYPE},$A{{r}})", "=IFERROR(B{r}/C{r},0)"],
      ["#,##0", "#,##0", "#,##0.00"],
      "Row order = highest to lowest total sales when the file was built.")

table("outlet", "Individual Outlet Performance", ["Outlet", "Total Sales", "Records", "% of Total Sales"],
      by("Outlet_Identifier"),
      [f"=SUMIFS({SALES},{OUTLET_ID},$A{{r}})", f"=COUNTIFS({OUTLET_ID},$A{{r}})",
       f"=IFERROR(B{{r}}/SUM({SALES}),0)"],
      ["#,##0", "#,##0", "0.0%"])

table("category", "Item Category Performance", ["Item Category", "Total Sales", "Records", "% of Total Sales"],
      by("Item_Category"),
      [f"=SUMIFS({SALES},{CATEGORY},$A{{r}})", f"=COUNTIFS({CATEGORY},$A{{r}})",
       f"=IFERROR(B{{r}}/SUM({SALES}),0)"],
      ["#,##0", "#,##0", "0.0%"])

table("tier", "City Tier Performance", ["City Tier", "Avg Sales per Record", "Total Sales", "Records"],
      sorted(df["Outlet_Location_Type"].unique()),
      [f"=IFERROR(AVERAGEIFS({SALES},{TIER},$A{{r}}),0)", f"=SUMIFS({SALES},{TIER},$A{{r}})",
       f"=COUNTIFS({TIER},$A{{r}})"],
      ["#,##0.00", "#,##0", "#,##0"])

top_types = df.groupby("Item_Type")["Item_Outlet_Sales"].sum().sort_values(ascending=False).head(10).index.tolist()
table("itemtype", "Top 10 Item Types", ["Item Type", "Total Sales", "Records"],
      top_types,
      [f"=SUMIFS({SALES},{ITEM_TYPE},$A{{r}})", f"=COUNTIFS({ITEM_TYPE},$A{{r}})"],
      ["#,##0", "#,##0"],
      "The ten item types are the top ten by sales when the file was built.")

table("mrp", "MRP Tier Performance", ["MRP Tier", "Avg MRP", "Avg Sales per Record", "Total Sales"],
      ["Low", "Medium", "High", "Premium"],
      [f"=IFERROR(AVERAGEIFS({MRP},{MRP_TIER},$A{{r}}),0)", f"=IFERROR(AVERAGEIFS({SALES},{MRP_TIER},$A{{r}}),0)",
       f"=SUMIFS({SALES},{MRP_TIER},$A{{r}})"],
      ["#,##0.00", "#,##0.00", "#,##0"],
      "Tiers: Low up to 70, Medium 70-140, High 140-210, Premium above 210 (MRP in rupees).")

# Visibility buckets: lower and upper limits sit in columns E and F so the formulas can reference them
vis_labels = ["Low (<5%)", "Medium (5-10%)", "High (10-15%)", "Very High (15%+)"]
vis_limits = [(0, 0.05), (0.05, 0.10), (0.10, 0.15), (0.15, 1.01)]
table("vis", "Visibility Bucket Performance", ["Visibility Bucket", "Avg Sales per Record", "Records", "Total Sales"],
      vis_labels,
      [f"=IFERROR(AVERAGEIFS({SALES},{VIS},\">=\"&$E{{r}},{VIS},\"<\"&$F{{r}}),0)",
       f"=COUNTIFS({VIS},\">=\"&$E{{r}},{VIS},\"<\"&$F{{r}})",
       f"=SUMIFS({SALES},{VIS},\">=\"&$E{{r}},{VIS},\"<\"&$F{{r}})"],
      ["#,##0.00", "#,##0", "#,##0"],
      "Lower limit (column E) is included, upper limit (column F) is excluded.")
v0, v1 = positions["vis"]
summ.cell(row=v0 - 1, column=5, value="Lower limit").font = head_font
summ.cell(row=v0 - 1, column=6, value="Upper limit").font = head_font
for c in (5, 6):
    summ.cell(row=v0 - 1, column=c).fill = navy_fill
for k, (lo, hi) in enumerate(vis_limits):
    for col, val in ((5, lo), (6, hi)):
        cell = summ.cell(row=v0 + k, column=col, value=val)
        cell.font, cell.border, cell.number_format = Font(name=FONT, size=10, color="0000FF"), box, "0.00"

table("year", "Outlet Establishment Year Performance", ["Year", "Avg Sales per Record", "Total Sales", "Records"],
      sorted(df["Outlet_Establishment_Year"].unique().tolist()),
      [f"=IFERROR(AVERAGEIFS({SALES},{YEAR},$A{{r}}),0)", f"=SUMIFS({SALES},{YEAR},$A{{r}})",
       f"=COUNTIFS({YEAR},$A{{r}})"],
      ["#,##0.00", "#,##0", "#,##0"])

# Headline numbers used by the dashboard cards (column I/J, top right of the Summary sheet)
summ["I4"] = "Headline Numbers"
summ["I4"].font = Font(name=FONT, size=11, bold=True, color=NAVY)
o_first, o_last = positions["outlet"]
kpis = [
    ("Total Sales (₹)", f"=SUM({SALES})", "#,##0"),
    ("Records", f"=COUNTA({rng('Item_Identifier')})", "#,##0"),
    ("Unique Products", f"=SUMPRODUCT(1/COUNTIF({rng('Item_Identifier')},{rng('Item_Identifier')}))", "#,##0"),
    ("Outlets", f"=COUNTA($A${o_first}:$A${o_last})", "#,##0"),
]
for k, (label, formula, fmt) in enumerate(kpis):
    r = 5 + k
    a, b = summ.cell(row=r, column=9, value=label), summ.cell(row=r, column=10, value=formula)
    a.font, b.font, b.number_format = body_font, bold_font, fmt
    a.border = b.border = box
KPI_CELLS = [f"Summary!$J${5 + k}" for k in range(4)]

for col, width in zip("ABCDEFGHIJ", [30, 20, 18, 22, 14, 14, 4, 4, 20, 18]):
    summ.column_dimensions[col].width = width

# ------------------------------------------------------------------- Dashboard
dash.sheet_view.showGridLines = False
for col in "ABCDEFGHIJKLMNOPQ":
    dash.column_dimensions[col].width = 9.5
dash.merge_cells("A1:P1")
dash["A1"] = "Big Mart Sales — Executive Dashboard"
dash["A1"].font, dash["A1"].fill = title_font, navy_fill
dash["A1"].alignment = Alignment(horizontal="center", vertical="center")
dash.row_dimensions[1].height = 30
dash.merge_cells("A2:P2")
dash["A2"] = (f"Public retail dataset | {N:,} item-outlet records | recorded 2013 sales "
              f"(not profit) | all figures are formulas over the Data sheet")
dash["A2"].font = note_font
dash["A2"].alignment = Alignment(horizontal="center")

card_ranges = ["A4:D4", "E4:H4", "I4:L4", "M4:P4"]
for k, (label, _, fmt) in enumerate(kpis):
    top = card_ranges[k]
    first_col, last_col = top.split(":")[0][0], top.split(":")[1][0]
    dash.merge_cells(f"{first_col}4:{last_col}4")
    dash.merge_cells(f"{first_col}5:{last_col}5")
    h, v = dash[f"{first_col}4"], dash[f"{first_col}5"]
    h.value, v.value = label, f"={KPI_CELLS[k]}"
    h.font, h.fill, h.alignment = head_font, navy_fill, Alignment(horizontal="center")
    v.font, v.fill, v.number_format = Font(name=FONT, size=16, bold=True, color=NAVY), light_fill, fmt
    v.alignment = Alignment(horizontal="center", vertical="center")
dash.row_dimensions[5].height = 30


def add_chart(name, title, cats_col, vals_col, anchor, horizontal=False, y_title=None, fmt="#,##0", width=14.6, height=7.4):
    first, last = positions[name]
    chart = BarChart()
    chart.type = "bar" if horizontal else "col"
    chart.title = title
    chart.style = 10
    chart.legend = None
    chart.roundedCorners = False
    chart.title.overlay = False
    chart.add_data(Reference(summ, min_col=vals_col, min_row=first, max_row=last), titles_from_data=False)
    chart.set_categories(Reference(summ, min_col=cats_col, min_row=first, max_row=last))
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.y_axis.numFmt = fmt
    if horizontal:
        chart.x_axis.scaling.orientation = "maxMin"
    if y_title:
        chart.y_axis.title = y_title
        chart.y_axis.title.overlay = False
    chart.width, chart.height = width, height
    dash.add_chart(chart, anchor)


add_chart("type", "Total Sales by Outlet Type (₹)", 1, 2, "A7")
add_chart("tier", "Average Sales per Record by City Tier (₹)", 1, 2, "I7", fmt="#,##0")
add_chart("category", "Total Sales by Item Category (₹)", 1, 2, "A23")
add_chart("itemtype", "Top 10 Item Types by Total Sales (₹)", 1, 2, "I23", horizontal=True)
add_chart("mrp", "Average Sales per Record by MRP Tier (₹)", 1, 3, "A39")
add_chart("vis", "Average Sales per Record by Visibility Bucket (₹)", 1, 2, "I39")
add_chart("outlet", "Total Sales by Outlet (₹)", 1, 2, "A55", horizontal=True, width=29.4, height=8.5)
add_chart("year", "Average Sales per Record by Establishment Year (₹)", 1, 2, "A73", width=29.4, height=7.4)

dash.page_setup.orientation = "portrait"
dash.page_setup.fitToWidth = 1
dash.page_setup.fitToHeight = 0
dash.sheet_properties.pageSetUpPr.fitToPage = True

# ---------------------------------------------------------------- Data Quality
quality.append(["Check", "Value", "Note"])
rows = [
    ("Raw rows", 8523, "From the cleaning script output"),
    ("Exact duplicate rows removed", 0, "From the cleaning script output"),
    ("Missing Item_Weight before cleaning", 1463, "Filled from the same product in other outlets, then item-type median"),
    ("Missing Outlet_Size before cleaning", 2410, "Three whole outlets (OUT010, OUT017, OUT045) have no size; filled with the most common size for their outlet type"),
    ("Zero Item_Visibility before cleaning", 526, "Zero is not realistic for a stocked item; treated as missing and filled"),
    ("Final rows (formula)", f"=COUNTA({rng('Item_Identifier')})", "Counted live from the Data sheet"),
    ("Final columns", len(df.columns), "17 columns: 12 original plus 5 derived"),
    ("Blank cells in Data sheet (formula)", f"=COUNTBLANK(Data!$A$2:${get_column_letter(len(df.columns))}${LAST})", "Expect 0"),
    ("Records with a filled-in Outlet_Size (formula)", f"=COUNTIF({rng('Outlet_Size_Imputed')},\"Yes\")", "Outlet-size comparisons rest on these assumptions for about 28% of records"),
]
for r in rows:
    quality.append(list(r))
quality.append([])
quality.append(["Dataset source", "BigMart Sales dataset (Analytics Vidhya \"Big Mart Sales III\"), shared on Kaggle by Yasser H"])
quality.append(["Source URL", "https://www.kaggle.com/datasets/yasserh/bigmartsalesdataset"])
source_link = quality[quality.max_row][1]
source_link.hyperlink = source_link.value
source_link.style = "Hyperlink"
quality.append(["Attribution note", "Raw data belongs to its publishers. Cleaned data and all analysis outputs are derived in this project."])
for cell in quality[1]:
    cell.font, cell.fill = head_font, navy_fill
for row in quality.iter_rows(min_row=2):
    for cell in row:
        cell.font = body_font
        cell.alignment = Alignment(wrap_text=True, vertical="top")
for col, width in zip("ABC", [46, 28, 80]):
    quality.column_dimensions[col].width = width

OUT_PATH.parent.mkdir(exist_ok=True)
wb.save(OUT_PATH)
print(f"Saved {OUT_PATH.relative_to(ROOT)}")
