"""
=============================================================================
法國 Provence 產區葡萄酒供需平衡模型
Supply-Demand Balance Model for Provence Wine Region
=============================================================================

等式: 期末庫存 = 期初庫存 + 產量 - 出莊量 - 損耗
推估銷售: 推估銷售 ≈ 期初庫存 + 產量 - 期末庫存

資料來源 (全部來自 douane.gouv.fr):
  A類: Campagne viti-vinicole — 月度出莊量 + 商業庫存
  B類: Stocks à la production — 年度生產庫存 (7月底)
  C類: Production des vins — 年度產量申報
"""

import pandas as pd
import numpy as np
import re
import os
import warnings
warnings.filterwarnings('ignore')

ROOT = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR = os.path.join(ROOT, "raw_data", "Frace", "Stocks")
PROD_DIR = os.path.join(ROOT, "raw_data", "Frace", "Production")
OUTPUT_DIR = os.path.join(ROOT, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# 1. 解析 B 類: 生產庫存
# ============================================================================

STOCK_FILES = {
    "2019-2020": "2020.07.31 - Stocks à la production et au commerce - Déclaration de stock 2019-2020.xlsx",
    "2020-2021": "Stocks à la production et au commerce - Déclaration de stock 2020-2021 pour DATADOUANE.xlsx",
    "2021-2022": "Stocks à la production et au commerce - Déclaration de stock 2021-2022 pour DATADOUANE.xlsx",
    "2022-2023": "Stocks à la production et au commerce - Déclaration de stock 2022-2023 pour DATADOUANE_0.xlsx",
    "2023-2024": "Stocks à la production et au commerce - Déclaration de stock 2023-2024 pour DATADOUANE.xlsx",
    "2024-2025": "Stocks à la production et au commerce - Déclaration de stock 2024-2025 pour DATADOUANE.xlsx",
}

def parse_stock_file(filepath: str, campagne: str) -> pd.DataFrame:
    """
    解析生產庫存彙總表
    Sheet 1 (Stocks à la production): 按 dept × 類別 × 顏色
    
    欄位:
      Col 0: dept_code, Col 1: dept_name, Col 2: nb_declarants
      Cols 3-5: AOP (blanc, rosé, rouge)
      Cols 6-8: IGP avec cépage (b, r, rg)
      Cols 9-11: IGP sans cépage (b, r, rg)
      Cols 12-14: VSIG avec cépage (b, r, rg)
      Cols 15-17: VSIG sans cépage (b, r, rg)
      Col 18: TOTAUX
    """
    xls = pd.ExcelFile(filepath, engine='openpyxl')
    # 找 "Stocks à la production" 的 sheet
    prod_sheet = [s for s in xls.sheet_names if 'production' in s.lower()][0]
    df = pd.read_excel(xls, sheet_name=prod_sheet, header=None)
    
    records = []
    for i in range(14, len(df)):
        dept_code = df.iloc[i, 0]
        if pd.isna(dept_code):
            continue
        dept_code = str(dept_code).strip().zfill(2)
        if not dept_code.isdigit():
            continue
        
        def safe(col):
            v = df.iloc[i, col] if col < df.shape[1] else 0
            return float(v) if pd.notna(v) else 0.0
        
        rec = {
            'campagne': campagne,
            'dept_code': dept_code,
            'dept_name': str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else '',
            'nb_declarants': safe(2),
            # AOP
            'stock_aop_blanc': safe(3),
            'stock_aop_rose': safe(4),
            'stock_aop_rouge': safe(5),
            # IGP (avec + sans cépage)
            'stock_igp_blanc': safe(6) + safe(9),
            'stock_igp_rose': safe(7) + safe(10),
            'stock_igp_rouge': safe(8) + safe(11),
            # VSIG (avec + sans cépage)
            'stock_vsig_blanc': safe(12) + safe(15),
            'stock_vsig_rose': safe(13) + safe(16),
            'stock_vsig_rouge': safe(14) + safe(17),
            # Total
            'stock_production_total': safe(18),
        }
        # 計算合計
        rec['stock_aop_total'] = rec['stock_aop_blanc'] + rec['stock_aop_rose'] + rec['stock_aop_rouge']
        rec['stock_igp_total'] = rec['stock_igp_blanc'] + rec['stock_igp_rose'] + rec['stock_igp_rouge']
        rec['stock_vsig_total'] = rec['stock_vsig_blanc'] + rec['stock_vsig_rose'] + rec['stock_vsig_rouge']
        rec['stock_rose_total'] = rec['stock_aop_rose'] + rec['stock_igp_rose'] + rec['stock_vsig_rose']
        rec['stock_rouge_total'] = rec['stock_aop_rouge'] + rec['stock_igp_rouge'] + rec['stock_vsig_rouge']
        rec['stock_blanc_total'] = rec['stock_aop_blanc'] + rec['stock_igp_blanc'] + rec['stock_vsig_blanc']
        
        records.append(rec)
    
    return pd.DataFrame(records)


print("📦 解析 B 類: 生產庫存...")
dfs_stock = []
for camp, fn in STOCK_FILES.items():
    fp = os.path.join(STOCK_DIR, fn)
    if os.path.exists(fp):
        d = parse_stock_file(fp, camp)
        dfs_stock.append(d)
        print(f"  ✅ {camp}: {len(d)} départements")
    else:
        print(f"  ⚠️ {camp}: 檔案不存在 ({fn})")

df_stock_prod = pd.concat(dfs_stock, ignore_index=True)
print(f"  → 合計 {len(df_stock_prod)} 筆")


# ============================================================================
# 2. 解析 C 類: 產量
# ============================================================================

PROD_FILES = {
    "2019": "2019 - Relevé par département de la production des vins.xlsx",
    # "2020": 本機 raw_data/Frace/Production/ 沒有 2020 年那份檔，先略過
    "2021": "2021 - Relevé par département de la production des vins dépt 32 rectifié.xlsx",
    "2022": "2022 - Relevé par département de la production des vins dépt 32 rectifié.xlsx",
    "2023": "2023 - Relevé par département de la production des vins OPENDATA rectifié au 08-07-2024.xlsx",
    "2024": "2024 - Relevé par département de la production des vins OPENDATA.xlsx",
}

def extract_dept_code_production(s: str) -> str:
    """從 '13 BOUCHES-DU-RHONE' 提取 '13'"""
    if pd.isna(s):
        return ''
    s = str(s).strip()
    match = re.match(r'^[O0]?(\d{1,2})\b', s)
    return match.group(1).zfill(2) if match else ''

def parse_production_file(filepath: str, year: str) -> pd.DataFrame:
    """
    解析產量彙總表
    
    關鍵欄位 (位置可能因年份略有差異):
      Col 0: Département
      Col 1: 申報數
      Col 2: 葡萄園面積 (ha)
      Cols 7-9: AOP (blanc, rouge, rosé) in hl
      Cols 11-13: IGP (blanc, rouge, rosé) in hl
      Cols 14-16: VSIG (blanc, rouge, rosé) in hl
      Col 18: Production commercialisable (hl)
      Col 20: TOTAL (hl)
    """
    engine = 'xlrd' if filepath.endswith('.xls') else 'openpyxl'
    df = pd.read_excel(filepath, header=None, engine=engine)
    
    # 找到資料起始行 (département 格式: "01 AIN" 或 "O1 AIN")
    start = -1
    for i in range(len(df)):
        code = extract_dept_code_production(df.iloc[i, 0])
        if code == '01':
            start = i
            break
    
    if start < 0:
        print(f"    ⚠️ 找不到起始行")
        return pd.DataFrame()
    
    records = []
    for i in range(start, len(df)):
        dept_code = extract_dept_code_production(df.iloc[i, 0])
        if not dept_code:
            continue
        
        def safe(col):
            v = df.iloc[i, col] if col < df.shape[1] else 0
            return float(v) if pd.notna(v) else 0.0
        
        # 對應的 campagne (產量年份 2019 → campagne 2019-2020)
        campagne = f"{year}-{int(year)+1}"
        
        rec = {
            'campagne': campagne,
            'harvest_year': int(year),
            'dept_code': dept_code,
            'dept_name': str(df.iloc[i, 0]).strip(),
            'nb_declarations': safe(1),
            'superficie_totale_ha': safe(2),
            # AOP 產量
            'prod_aop_blanc': safe(7),
            'prod_aop_rouge': safe(8),
            'prod_aop_rose': safe(9),
            # IGP 產量
            'prod_igp_blanc': safe(11),
            'prod_igp_rouge': safe(12),
            'prod_igp_rose': safe(13),
            # VSIG 產量
            'prod_vsig_blanc': safe(14),
            'prod_vsig_rouge': safe(15),
            'prod_vsig_rose': safe(16),
            # 總計
            'prod_commercialisable': safe(18),
            'prod_total': safe(20) if df.shape[1] > 20 else safe(18),
        }
        
        # 計算合計
        rec['prod_aop_total'] = rec['prod_aop_blanc'] + rec['prod_aop_rouge'] + rec['prod_aop_rose']
        rec['prod_igp_total'] = rec['prod_igp_blanc'] + rec['prod_igp_rouge'] + rec['prod_igp_rose']
        rec['prod_vsig_total'] = rec['prod_vsig_blanc'] + rec['prod_vsig_rouge'] + rec['prod_vsig_rose']
        rec['prod_rose_total'] = rec['prod_aop_rose'] + rec['prod_igp_rose'] + rec['prod_vsig_rose']
        
        records.append(rec)
    
    return pd.DataFrame(records)


print("\n🍇 解析 C 類: 產量...")
dfs_prod = []
for year, fn in PROD_FILES.items():
    fp = os.path.join(PROD_DIR, fn)
    if os.path.exists(fp):
        d = parse_production_file(fp, year)
        dfs_prod.append(d)
        print(f"  ✅ {year}: {len(d)} départements")
    else:
        print(f"  ⚠️ {year}: 檔案不存在 ({fn})")

df_production = pd.concat(dfs_prod, ignore_index=True)
print(f"  → 合計 {len(df_production)} 筆")


# ============================================================================
# 3. 讀取已處理的 A 類資料
# ============================================================================

print("\n📊 讀取 A 類: 出莊量...")
df_sortie_annual = pd.read_csv(os.path.join(OUTPUT_DIR, "wine_annual_summary.csv"))
df_stock_commerce = pd.read_csv(os.path.join(OUTPUT_DIR, "wine_stock_commerce.csv"))
print(f"  ✅ 年度出莊: {len(df_sortie_annual)} 筆")
print(f"  ✅ 商業庫存: {len(df_stock_commerce)} 筆")


# ============================================================================
# 4. 建構供需 Panel
# ============================================================================

print("\n🔗 建構供需平衡 Panel...")

# 4a. 從 B 類取生產庫存
stock_panel = df_stock_prod[['campagne', 'dept_code', 'stock_production_total',
                              'stock_aop_total', 'stock_igp_total', 'stock_vsig_total',
                              'stock_rose_total', 'stock_rouge_total', 'stock_blanc_total',
                              'nb_declarants']].copy()

# 4b. 從 C 類取產量
prod_panel = df_production[['campagne', 'dept_code', 
                             'prod_commercialisable', 'prod_total',
                             'prod_aop_total', 'prod_igp_total', 'prod_vsig_total',
                             'prod_rose_total', 'superficie_totale_ha']].copy()

# 4c. 從 A 類取年度出莊量 (161A 7月 YTD)
sortie_panel = df_sortie_annual[['campagne', 'dept_code', 'annual_sortie_hl']].copy()

# 4d. 從 A 類取 7 月底商業庫存
stock_comm = df_stock_commerce[df_stock_commerce['month'] == 7][
    ['campagne', 'dept_code', 'stock_commerce']
].copy()

# 統一 dept_code 為字串
for d in [stock_panel, prod_panel, sortie_panel, stock_comm]:
    d['dept_code'] = d['dept_code'].astype(str).str.zfill(2)

# 合併
panel = stock_panel.merge(prod_panel, on=['campagne', 'dept_code'], how='outer')
panel = panel.merge(sortie_panel, on=['campagne', 'dept_code'], how='outer')
panel = panel.merge(stock_comm, on=['campagne', 'dept_code'], how='left')

# 4e. 計算期初庫存 (= 上一 campagne 的期末庫存)
panel = panel.sort_values(['dept_code', 'campagne']).reset_index(drop=True)
panel['stock_start'] = panel.groupby('dept_code')['stock_production_total'].shift(1)

# 4f. 供需等式計算
# 推估銷售 = 期初庫存 + 產量 - 期末庫存
panel['implied_absorption'] = (
    panel['stock_start'] + panel['prod_commercialisable'] - panel['stock_production_total']
)

# 出莊量 vs 推估吸收量 的差異 ≈ 損耗 + 調撥 + 蒸發
panel['gap_sortie_vs_absorption'] = panel['annual_sortie_hl'] - panel['implied_absorption']

# 庫存周轉率 (月) = 期末生產庫存 / (年出莊量 / 12)
panel['stock_turnover_months'] = np.where(
    panel['annual_sortie_hl'] > 0,
    panel['stock_production_total'] / (panel['annual_sortie_hl'] / 12),
    np.nan
)

# 庫銷比 = 期末庫存 / 年出莊量
panel['stock_to_sortie_ratio'] = np.where(
    panel['annual_sortie_hl'] > 0,
    panel['stock_production_total'] / panel['annual_sortie_hl'],
    np.nan
)

# 單位面積產量 (hl/ha)
panel['yield_hl_per_ha'] = np.where(
    panel['superficie_totale_ha'] > 0,
    panel['prod_commercialisable'] / panel['superficie_totale_ha'],
    np.nan
)

# Rosé 佔比
panel['rose_pct_production'] = np.where(
    panel['prod_commercialisable'] > 0,
    panel['prod_rose_total'] / panel['prod_commercialisable'] * 100,
    np.nan
)
panel['rose_pct_stock'] = np.where(
    panel['stock_production_total'] > 0,
    panel['stock_rose_total'] / panel['stock_production_total'] * 100,
    np.nan
)

print(f"  → Panel 建構完成: {len(panel)} 筆, {panel['dept_code'].nunique()} 個 département")


# ============================================================================
# 5. Provence 分析
# ============================================================================

PROV = ['13', '83']
COMPARE = ['33', '34', '84']  # Gironde(Bordeaux), Hérault(Languedoc), Vaucluse

prov = panel[panel['dept_code'].isin(PROV)].copy()
comp = panel[panel['dept_code'].isin(PROV + COMPARE)].copy()

print("\n" + "=" * 70)
print("🍷 PROVENCE 供需平衡分析")
print("=" * 70)

# 5a. 供需總覽
print("\n【供需總覽 — Var (83)】")
var = prov[prov['dept_code'] == '83'].sort_values('campagne')
cols_show = ['campagne', 'prod_commercialisable', 'annual_sortie_hl', 
             'stock_production_total', 'stock_start', 'implied_absorption',
             'stock_turnover_months']
print(var[cols_show].to_string(index=False, float_format='{:,.0f}'.format))

print("\n【供需總覽 — Bouches-du-Rhône (13)】")
bdr = prov[prov['dept_code'] == '13'].sort_values('campagne')
print(bdr[cols_show].to_string(index=False, float_format='{:,.0f}'.format))

# 5b. 庫存周轉率比較
print("\n\n【庫存周轉率比較 (月) — 越低表示去化越快】")
turnover = comp.pivot_table(
    index='campagne', columns='dept_code', values='stock_turnover_months'
)
col_names = {'13': 'BdR(13)', '33': 'Bordeaux(33)', '34': 'Languedoc(34)',
             '83': 'Var(83)', '84': 'Vaucluse(84)'}
turnover = turnover.rename(columns=col_names)
print(turnover.round(1).to_string())

# 5c. Rosé 結構
print("\n\n【Rosé 佔生產量比例 (%)】")
rose_prod = comp.pivot_table(
    index='campagne', columns='dept_code', values='rose_pct_production'
)
rose_prod = rose_prod.rename(columns=col_names)
print(rose_prod.round(1).to_string())

# 5d. Rosé 佔庫存比例
print("\n\n【Rosé 佔生產庫存比例 (%)】")
rose_stock = comp.pivot_table(
    index='campagne', columns='dept_code', values='rose_pct_stock'
)
rose_stock = rose_stock.rename(columns=col_names)
print(rose_stock.round(1).to_string())

# 5e. 單位面積產量
print("\n\n【單位面積產量 (hl/ha)】")
yield_ha = comp.pivot_table(
    index='campagne', columns='dept_code', values='yield_hl_per_ha'
)
yield_ha = yield_ha.rename(columns=col_names)
print(yield_ha.round(1).to_string())

# 5f. 供需平衡指標
print("\n\n【供需平衡指標 — Var (83)】")
print("  推估吸收量 = 期初庫存 + 產量 - 期末庫存")
print("  差異 = 出莊量 - 推估吸收量 (>0 表示出莊 > 吸收, 可能有調撥流入)")
var_balance = var[['campagne', 'stock_start', 'prod_commercialisable', 
                    'stock_production_total', 'implied_absorption',
                    'annual_sortie_hl', 'gap_sortie_vs_absorption']].copy()
var_balance.columns = ['Campagne', '期初庫存', '產量', '期末庫存', 
                        '推估吸收', '出莊量', '差異']
print(var_balance.to_string(index=False, float_format='{:,.0f}'.format))

# 5g. Provence vs 全法比較
print("\n\n【Provence vs 全法 — 出莊量佔比 (%)】")
total_france = panel.groupby('campagne')['annual_sortie_hl'].sum()
prov_total = prov.groupby('campagne')['annual_sortie_hl'].sum()
share = (prov_total / total_france * 100).round(2)
print(share.to_string())


# ============================================================================
# 6. 匯出
# ============================================================================

# 完整 panel
panel_out = os.path.join(OUTPUT_DIR, "wine_supply_demand_panel.csv")
panel.to_csv(panel_out, index=False, encoding='utf-8-sig')
print(f"\n💾 供需 Panel: {panel_out}")

# Provence 詳細
prov_out = os.path.join(OUTPUT_DIR, "wine_provence_supply_demand.csv")
prov.to_csv(prov_out, index=False, encoding='utf-8-sig')
print(f"💾 Provence 供需: {prov_out}")

# 跨產區比較
comp_out = os.path.join(OUTPUT_DIR, "wine_region_comparison.csv")
comp.to_csv(comp_out, index=False, encoding='utf-8-sig')
print(f"💾 跨產區比較: {comp_out}")

# 生產庫存原始
stock_out = os.path.join(OUTPUT_DIR, "wine_stock_production_all.csv")
df_stock_prod.to_csv(stock_out, index=False, encoding='utf-8-sig')
print(f"💾 生產庫存原始: {stock_out}")

# 產量原始
prod_out = os.path.join(OUTPUT_DIR, "wine_production_all.csv")
df_production.to_csv(prod_out, index=False, encoding='utf-8-sig')
print(f"💾 產量原始: {prod_out}")

print("\n✅ 供需平衡模型完成!")
