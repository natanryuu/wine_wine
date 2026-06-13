"""
🧹 UN Comtrade 葡萄酒原始資料清理
==================================
輸入：raw_data/UN/UNdata_Export_*.csv（多檔）
輸出：data/un_comtrade_wine_clean.csv

主要工作：
  1. 合併三個原始 CSV
  2. 重新命名欄位為 snake_case
  3. 衍生 commodity_short（4 大類）
  4. 衍生 volume_litres（含 kg → L 的 fallback）
  5. 衍生 price_per_litre 與 price_per_bottle_750ml
"""

import os
import glob
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(ROOT, "raw_data", "UN")
OUT_DIR = os.path.join(ROOT, "data")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_CSV = os.path.join(OUT_DIR, "un_comtrade_wine_clean.csv")

# 葡萄酒密度約 1.0 kg/L（紅/白都接近 0.99，散裝可能略低，這裡用 1.0 簡化）
KG_PER_LITRE = 1.0

# Commodity 全名 → 短代號
COMMODITY_MAP = {
    "Wine; sparkling": "Sparkling",
    "Wine; still, in containers holding 2 litres or less": "Still_Bottled",
    "Wine; still, in containers holding more than 2 litres but not more than 10 litres": "Still_2to10L",
    "Wine; still, in containers holding more than 10 litres": "Still_Bulk",
}


def derive_volume_litres(row):
    """
    依 qty_name 換算成公升：
      - 'Volume in litres'      → 直接用 quantity
      - 'Weight in kilograms'   → quantity / KG_PER_LITRE
      - 'No Quantity' / 其他    → 用 weight_kg fallback
      - 都缺                    → NaN
    """
    qty_name = row.get('qty_name')
    qty = row.get('quantity')
    weight = row.get('weight_kg')

    if pd.notna(qty) and qty > 0:
        if qty_name == 'Volume in litres':
            return qty
        if qty_name == 'Weight in kilograms':
            return qty / KG_PER_LITRE

    if pd.notna(weight) and weight > 0:
        return weight / KG_PER_LITRE

    return np.nan


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "UNdata_Export_*.csv")))
    if not files:
        raise FileNotFoundError(f"找不到原始檔，請確認 {RAW_DIR} 有 UNdata_Export_*.csv")

    print(f"🔍 找到 {len(files)} 個原始檔：")
    for f in files:
        print(f"   - {os.path.basename(f)}")

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"\n📊 合併總筆數: {len(df):,}")

    # 1. 重新命名為 snake_case
    df = df.rename(columns={
        'Country or Area': 'country',
        'Year': 'year',
        'Commodity': 'commodity',
        'Flow': 'flow',
        'Trade (USD)': 'trade_usd',
        'Weight (kg)': 'weight_kg',
        'Quantity Name': 'qty_name',
        'Quantity': 'quantity',
    })

    # 2. 數值欄位轉型（quantity 可能是空字串）
    for col in ['trade_usd', 'weight_kg', 'quantity']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['year'] = df['year'].astype(int)

    # 3. 國家標準化
    df['country'] = df['country'].replace({
        'United States': 'USA',
        'US': 'USA',
    })

    # 4. 衍生 commodity_short
    df['commodity_short'] = df['commodity'].map(COMMODITY_MAP)
    unmapped = df[df['commodity_short'].isna()]['commodity'].unique()
    if len(unmapped) > 0:
        print(f"\n⚠️  發現未對應的 commodity:")
        for u in unmapped:
            print(f"   - {u}")

    # 5. 衍生 volume_litres
    df['volume_litres'] = df.apply(derive_volume_litres, axis=1)

    # 6. 衍生單價
    df['price_per_litre'] = np.where(
        (df['volume_litres'] > 0) & df['trade_usd'].notna(),
        df['trade_usd'] / df['volume_litres'],
        np.nan
    )
    df['price_per_bottle_750ml'] = df['price_per_litre'] * 0.75

    # 7. 重排欄位順序
    cols = [
        'country', 'year', 'commodity', 'flow',
        'trade_usd', 'weight_kg', 'qty_name', 'quantity',
        'commodity_short', 'volume_litres',
        'price_per_litre', 'price_per_bottle_750ml',
    ]
    df = df[cols]

    # 8. 輸出
    df.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n💾 已輸出: {OUT_CSV}")
    print(f"   總筆數: {len(df):,}")

    # 9. 簡單品質檢查
    print(f"\n🔎 資料品質檢查:")
    print(f"   trade_usd 缺值: {df['trade_usd'].isna().sum()} 筆")
    print(f"   volume_litres 缺值: {df['volume_litres'].isna().sum()} 筆")
    print(f"   price_per_litre 缺值: {df['price_per_litre'].isna().sum()} 筆")

    print(f"\n📋 commodity_short × flow 交叉表:")
    ct = pd.crosstab(df['commodity_short'], df['flow'])
    print(ct.to_string())

    print(f"\n🌍 各國筆數:")
    print(df['country'].value_counts().to_string())

    print(f"\n💰 單價合理性 sanity check（Still_Bottled 出口）:")
    sb = df[(df['flow'] == 'Export') & (df['commodity_short'] == 'Still_Bottled')]
    sb_price = sb.groupby('country')['price_per_bottle_750ml'].mean().sort_values(ascending=False)
    print(sb_price.round(2).head(15).to_string())

    print(f"\n🎉 清理完成！")


if __name__ == '__main__':
    main()
