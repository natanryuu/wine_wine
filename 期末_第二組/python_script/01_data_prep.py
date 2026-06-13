"""
============================================================================
Step 1: 資料準備與特徵工程
- 載入 4 個 CSV
- 篩出 Var (83) 與 BdR (13) - Provence 核心兩個部門
- 計算 sans_ig_ratio (品質稀釋指標)
- 建構年度特徵表 + 月度時序表
- 輸出: feature_table.csv, provence_monthly_long.csv
============================================================================
"""
import pandas as pd
import numpy as np
import os

DATA_DIR = "/mnt/user-data/uploads"
OUT_DIR  = "/home/claude/wine_final/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 1. 載入 ----------
raw     = pd.read_csv(f"{DATA_DIR}/wine_data_all_raw.csv")
annual  = pd.read_csv(f"{DATA_DIR}/wine_annual_summary.csv")
prov_m  = pd.read_csv(f"{DATA_DIR}/wine_provence_monthly.csv")
stock   = pd.read_csv(f"{DATA_DIR}/wine_stock_commerce.csv")

# 把 dept_code 統一補 0 (例如 1 -> "01")
for d in (raw, annual, prov_m, stock):
    d["dept_code"] = d["dept_code"].astype(str).str.zfill(2)

print(f"raw:    {raw.shape}  campagnes={sorted(raw['campagne'].unique())}")
print(f"annual: {annual.shape}")
print(f"prov_m: {prov_m.shape}")
print(f"stock:  {stock.shape}")

# ---------- 2. 計算每部門每年的結構比 ----------
# 7 月底的 161A 累計就是該 campagne 的全年總量
y_end = raw[(raw["report_type"] == "161A") & (raw["month"] == 7)].copy()

struct = (y_end.groupby(["campagne", "dept_code", "dept_name"])
                .agg(ig_total=("ig_total", "sum"),
                     sans_ig_total=("sans_ig_total", "sum"),
                     grand_total=("grand_total", "sum"))
                .reset_index())
struct["sans_ig_ratio"] = np.where(struct["grand_total"] > 0,
                                   struct["sans_ig_total"] / struct["grand_total"], 0)
struct["ig_ratio"]      = np.where(struct["grand_total"] > 0,
                                   struct["ig_total"]      / struct["grand_total"], 0)

# 解析 AOP / IGP 各自比例 (期末新增的細緻指標)
aop_igp = (y_end.groupby(["campagne", "dept_code"])
                .agg(aop_total=("aop_month",  "sum"),    # 7月是YTD,所以 month 值就是累計
                     igp_total=("igp_month",  "sum"))
                .reset_index())
# 註: 7月的 aop_month/igp_month 已包含全年累計 (因為是 YTD,但這裡是月度欄位)
# 更穩健的做法: 把每月加總起來
aop_igp_robust = (raw[(raw["report_type"] == "161A")]
                  .groupby(["campagne", "dept_code"])
                  .agg(aop_year=("aop_month", "sum"),
                       igp_year=("igp_month", "sum"))
                  .reset_index())
struct = struct.merge(aop_igp_robust, on=["campagne", "dept_code"])
struct["aop_ratio"] = np.where(struct["grand_total"] > 0,
                               struct["aop_year"] / struct["grand_total"], 0)
struct["igp_ratio"] = np.where(struct["grand_total"] > 0,
                               struct["igp_year"] / struct["grand_total"], 0)

# ---------- 3. 庫存周轉 ----------
stock_july = (stock[stock["month"] == 7]
              .groupby(["campagne", "dept_code"])["stock_commerce"].sum()
              .reset_index().rename(columns={"stock_commerce": "stock_eoy_hl"}))

# ---------- 4. 合併成 feature table ----------
feat = struct.merge(stock_july, on=["campagne", "dept_code"], how="left")
feat["stock_turnover_months"] = np.where(feat["grand_total"] > 0,
                                         feat["stock_eoy_hl"] / (feat["grand_total"] / 12),
                                         np.nan)
feat["is_provence"]    = feat["dept_code"].isin(["13", "83"]).astype(int)
feat["is_var"]         = (feat["dept_code"] == "83").astype(int)
feat["campagne_start"] = feat["campagne"].str[:4].astype(int)

# 排序
feat = feat[["campagne", "campagne_start", "dept_code", "dept_name",
             "grand_total", "ig_total", "sans_ig_total",
             "ig_ratio", "sans_ig_ratio",
             "aop_year", "igp_year", "aop_ratio", "igp_ratio",
             "stock_eoy_hl", "stock_turnover_months",
             "is_provence", "is_var"]]

feat.to_csv(f"{OUT_DIR}/feature_table.csv", index=False)
print(f"\nfeature_table.csv saved ({feat.shape[0]} rows)")

# ---------- 5. Provence summary ----------
print("\n=== Provence 結構比 (Var=83, BdR=13) ===")
print(feat[feat["is_provence"] == 1]
      [["campagne", "dept_code", "grand_total",
        "aop_ratio", "igp_ratio", "sans_ig_ratio",
        "stock_turnover_months"]]
      .round(3).to_string(index=False))

# ---------- 6. Provence 月度 long table for STL ----------
prov_long = prov_m.copy()
prov_long["calendar_ym"] = pd.to_datetime(prov_long["calendar_ym"])
prov_long.to_csv(f"{OUT_DIR}/provence_monthly_long.csv", index=False)
print("\nprovence_monthly_long.csv saved")

print("\n[Step 1 done]")
