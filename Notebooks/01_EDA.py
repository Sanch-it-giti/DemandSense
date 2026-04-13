# ============================================================
# DemandSense — Phase 1: Exploratory Data Analysis (EDA)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Style ────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#F8F9FA",
    "axes.facecolor":   "#FFFFFF",
    "axes.grid":        True,
    "grid.color":       "#E0E0E0",
    "font.family":      "DejaVu Sans",
})
BLUE   = "#1F3F7A"
ORANGE = "#F47B20"
COLORS = [BLUE, ORANGE, "#2ECC71", "#E74C3C", "#9B59B6"]

# ── 1. LOAD DATA ─────────────────────────────────────────────
df = pd.read_csv("/mnt/user-data/uploads/Sample_-_Superstore.csv", encoding="latin-1")

print("=" * 55)
print("  DEMANDSENSE — DATASET OVERVIEW")
print("=" * 55)
print(f"  Rows        : {df.shape[0]:,}")
print(f"  Columns     : {df.shape[1]}")
print(f"  Memory      : {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
print()
print("── Column Types ──")
print(df.dtypes.to_string())
print()
print("── Missing Values ──")
print(df.isnull().sum()[df.isnull().sum() > 0].to_string() or "  None ✓")

# ── 2. CLEAN DATA ─────────────────────────────────────────────
df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  format="%m/%d/%Y")
df["Year"]       = df["Order Date"].dt.year
df["Month"]      = df["Order Date"].dt.month
df["YearMonth"]  = df["Order Date"].dt.to_period("M")
df["DaysToShip"] = (df["Ship Date"] - df["Order Date"]).dt.days

print("\n── Date Range ──")
print(f"  From : {df['Order Date'].min().date()}")
print(f"  To   : {df['Order Date'].max().date()}")
print(f"  Span : {df['Year'].nunique()} years  ({df['Year'].unique().tolist()})")

# ── 3. MONTHLY SALES TREND ────────────────────────────────────
monthly = df.groupby("YearMonth")["Sales"].sum().reset_index()
monthly["YearMonth_dt"] = monthly["YearMonth"].dt.to_timestamp()

fig, ax = plt.subplots(figsize=(14, 4))
ax.fill_between(monthly["YearMonth_dt"], monthly["Sales"],
                alpha=0.15, color=BLUE)
ax.plot(monthly["YearMonth_dt"], monthly["Sales"],
        color=BLUE, linewidth=2.2, marker="o", markersize=3)
ax.set_title("Monthly Sales Trend (2014 – 2017)", fontsize=14,
             fontweight="bold", color=BLUE, pad=12)
ax.set_xlabel("Month", fontsize=11)
ax.set_ylabel("Total Sales ($)", fontsize=11)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/01_monthly_sales_trend.png", dpi=150)
plt.close()
print("\n✓ Saved: 01_monthly_sales_trend.png")

# ── 4. SALES BY CATEGORY ──────────────────────────────────────
cat_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))

# Bar chart
axes[0].bar(cat_sales.index, cat_sales.values,
            color=[BLUE, ORANGE, "#2ECC71"], edgecolor="white", linewidth=1.2)
axes[0].set_title("Total Sales by Category", fontsize=13,
                  fontweight="bold", color=BLUE)
axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
for i, v in enumerate(cat_sales.values):
    axes[0].text(i, v + 8000, f"${v/1e6:.2f}M", ha="center",
                 fontsize=10, fontweight="bold")

# Pie chart
axes[1].pie(cat_sales.values, labels=cat_sales.index,
            colors=[BLUE, ORANGE, "#2ECC71"],
            autopct="%1.1f%%", startangle=140,
            wedgeprops=dict(edgecolor="white", linewidth=2))
axes[1].set_title("Category Share", fontsize=13,
                  fontweight="bold", color=BLUE)

plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/02_sales_by_category.png", dpi=150)
plt.close()
print("✓ Saved: 02_sales_by_category.png")

# ── 5. TOP 10 SUB-CATEGORIES ──────────────────────────────────
subcat = df.groupby("Sub-Category")["Sales"].sum().sort_values(ascending=True).tail(10)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(subcat.index, subcat.values,
               color=[ORANGE if v == subcat.max() else BLUE for v in subcat.values],
               edgecolor="white")
ax.set_title("Top 10 Sub-Categories by Sales", fontsize=13,
             fontweight="bold", color=BLUE)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
for bar, val in zip(bars, subcat.values):
    ax.text(val + 2000, bar.get_y() + bar.get_height()/2,
            f"${val/1e3:.0f}K", va="center", fontsize=9)
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/03_top_subcategories.png", dpi=150)
plt.close()
print("✓ Saved: 03_top_subcategories.png")

# ── 6. YEARLY GROWTH ──────────────────────────────────────────
yearly = df.groupby("Year").agg(
    Total_Sales=("Sales", "sum"),
    Total_Orders=("Order ID", "nunique"),
    Total_Quantity=("Quantity", "sum"),
    Total_Profit=("Profit", "sum")
).reset_index()
yearly["Profit_Margin"] = (yearly["Total_Profit"] / yearly["Total_Sales"] * 100).round(2)

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].bar(yearly["Year"], yearly["Total_Sales"],
            color=BLUE, edgecolor="white", linewidth=1.2)
axes[0].set_title("Yearly Revenue", fontsize=13, fontweight="bold", color=BLUE)
axes[0].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
for _, row in yearly.iterrows():
    axes[0].text(row["Year"], row["Total_Sales"] + 10000,
                 f"${row['Total_Sales']/1e6:.2f}M", ha="center",
                 fontsize=10, fontweight="bold")

axes[1].plot(yearly["Year"], yearly["Profit_Margin"],
             color=ORANGE, linewidth=2.5, marker="o", markersize=8)
axes[1].fill_between(yearly["Year"], yearly["Profit_Margin"],
                     alpha=0.15, color=ORANGE)
axes[1].set_title("Profit Margin % by Year", fontsize=13,
                  fontweight="bold", color=BLUE)
axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:.1f}%"))
for _, row in yearly.iterrows():
    axes[1].text(row["Year"], row["Profit_Margin"] + 0.1,
                 f"{row['Profit_Margin']}%", ha="center",
                 fontsize=10, fontweight="bold")

plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/04_yearly_growth.png", dpi=150)
plt.close()
print("✓ Saved: 04_yearly_growth.png")

# ── 7. SEASONALITY HEATMAP ────────────────────────────────────
pivot = df.pivot_table(values="Sales", index="Year",
                       columns="Month", aggfunc="sum")
pivot.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"]

fig, ax = plt.subplots(figsize=(13, 4))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
            linewidths=0.5, ax=ax,
            annot_kws={"size": 8},
            cbar_kws={"label": "Sales ($)"})
ax.set_title("Sales Seasonality Heatmap (Year × Month)",
             fontsize=13, fontweight="bold", color=BLUE, pad=12)
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/05_seasonality_heatmap.png", dpi=150)
plt.close()
print("✓ Saved: 05_seasonality_heatmap.png")

# ── 8. SEGMENT ANALYSIS ───────────────────────────────────────
seg = df.groupby("Segment").agg(
    Sales=("Sales","sum"), Profit=("Profit","sum"),
    Orders=("Order ID","nunique")).reset_index()

fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(seg))
w = 0.35
ax.bar(x - w/2, seg["Sales"]/1e6, w, label="Sales ($M)", color=BLUE)
ax.bar(x + w/2, seg["Profit"]/1e3, w, label="Profit ($K)", color=ORANGE)
ax.set_xticks(x); ax.set_xticklabels(seg["Segment"])
ax.set_title("Sales & Profit by Customer Segment",
             fontsize=13, fontweight="bold", color=BLUE)
ax.legend()
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/06_segment_analysis.png", dpi=150)
plt.close()
print("✓ Saved: 06_segment_analysis.png")

# ── 9. FEATURE ENGINEERING FOR ML ────────────────────────────
print("\n── Feature Engineering ──")
monthly_ml = df.groupby(["YearMonth"]).agg(
    Total_Sales=("Sales", "sum"),
    Total_Quantity=("Quantity", "sum"),
    Num_Orders=("Order ID", "nunique"),
    Avg_Discount=("Discount", "mean"),
    Total_Profit=("Profit", "sum")
).reset_index()

monthly_ml["YearMonth_dt"] = monthly_ml["YearMonth"].dt.to_timestamp()
monthly_ml = monthly_ml.sort_values("YearMonth_dt").reset_index(drop=True)

# Lag features
for lag in [1, 2, 3]:
    monthly_ml[f"Sales_Lag_{lag}"] = monthly_ml["Total_Sales"].shift(lag)

# Rolling features
monthly_ml["Rolling_3M_Avg"]    = monthly_ml["Total_Sales"].rolling(3).mean()
monthly_ml["Rolling_3M_Std"]    = monthly_ml["Total_Sales"].rolling(3).std()

# Time features
monthly_ml["Month_Num"]  = monthly_ml["YearMonth_dt"].dt.month
monthly_ml["Year_Num"]   = monthly_ml["YearMonth_dt"].dt.year
monthly_ml["Quarter"]    = monthly_ml["YearMonth_dt"].dt.quarter

monthly_ml_clean = monthly_ml.dropna().reset_index(drop=True)
monthly_ml_clean.to_csv("/mnt/user-data/outputs/monthly_features.csv", index=False)

print(f"  Feature dataset shape : {monthly_ml_clean.shape}")
print(f"  Columns               : {list(monthly_ml_clean.columns)}")
print(f"\n✓ Saved: monthly_features.csv")

# ── 10. SUMMARY STATS ─────────────────────────────────────────
print("\n" + "=" * 55)
print("  KEY BUSINESS INSIGHTS")
print("=" * 55)
print(f"  Total Revenue     : ${df['Sales'].sum():>12,.2f}")
print(f"  Total Profit      : ${df['Profit'].sum():>12,.2f}")
print(f"  Total Orders      : {df['Order ID'].nunique():>12,}")
print(f"  Total Products    : {df['Product Name'].nunique():>12,}")
print(f"  Unique Customers  : {df['Customer Name'].nunique():>12,}")
print(f"  Avg Order Value   : ${df.groupby('Order ID')['Sales'].sum().mean():>12,.2f}")
print(f"  Best Month        : {monthly.loc[monthly['Sales'].idxmax(), 'YearMonth']}")
print(f"  Best Category     : {cat_sales.idxmax()} (${cat_sales.max():,.0f})")
print("=" * 55)
print("\n✅ Phase 1 EDA Complete! All charts saved to outputs/")
