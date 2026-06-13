"""
============================================================================
Step 2a (REAL DATA): 載入 Kaggle Wine Enthusiast 真實資料 (130k 評論)
============================================================================
取代原本 02a_simulate_wine_data.py 的模擬流程。
保留同樣的輸出 schema (country, province, variety, points, price, is_provence_flag)
讓下游 02b → 03 完全不需要改動。
============================================================================
"""
import pandas as pd
import numpy as np
import os

RAW = "/mnt/user-data/uploads/winemag_full_130k.csv"
OUT = "/home/claude/wine_final/outputs/wine_enthusiast_simulated.csv"  # 保留同檔名,讓 02b 不用改

df = pd.read_csv(RAW)
print(f"Raw rows: {len(df):,}")

# ---------- 1. 必要欄位 & 缺值處理 ----------
need = ["country", "province", "variety", "points", "price"]
df = df[need].copy()

# price 是目標變數,缺失必須丟掉
before = len(df)
df = df.dropna(subset=["price"])
print(f"After dropna(price): {len(df):,}  (-{before-len(df):,} rows)")

# province / variety 缺失補 "Unknown"
df["province"] = df["province"].fillna("Unknown")
df["variety"]  = df["variety"].fillna("Unknown")
df["country"]  = df["country"].fillna("Unknown")

# 價格極端值處理:保留全部 (log1p 已能處理 skew),但記錄一下
print(f"Price range: ${df['price'].min():.0f} - ${df['price'].max():.0f}, median ${df['price'].median():.0f}")
print(f"Points range: {df['points'].min()} - {df['points'].max()}, mean {df['points'].mean():.2f}")

# ---------- 2. 建立 is_provence_flag ----------
df["is_provence_flag"] = ((df["country"] == "France") &
                           (df["province"] == "Provence")).astype(int)
print(f"Provence wines: {df['is_provence_flag'].sum():,} ({df['is_provence_flag'].mean()*100:.2f}%)")

# ---------- 3. 確認 schema 與 02b 對齊 ----------
out_cols = ["country", "province", "variety", "points", "price", "is_provence_flag"]
df = df[out_cols]
df.to_csv(OUT, index=False)
print(f"\nWrote {len(df):,} rows to {OUT}")
print(df.head(3).to_string())
