"""
=============================================================================
法國海關葡萄酒資料解析與 Provence 產區分析
French Customs (DGDDI) Wine Data Parser & Provence Analysis
=============================================================================

資料來源: https://www.douane.gouv.fr/la-douane/opendata/mots-cles/vigne-et-vin
- 161A = 出莊量 (Sorties des chais des récoltants et négociants vinificateurs)
- 161B = 流通稅申報量 (Droit de circulation) + 商業庫存 (Stock au commerce)

每個 campagne (8月-隔年7月) 有 12 個月的月度報表。
每月分 161A 和 161B 兩張表，8月份則合併為一張。

欄位結構 (9月-7月的 161A):
  Col 0: 部門 (Département)
  Col 1: AOP 當月值
  Col 2: IGP 當月值
  Col 3: IG 累計前期 (Antérieurs)
  Col 4: IG 小計 (Total YTD)
  Col 5: Sans IG 當月值
  Col 6: Sans IG 累計前期
  Col 7: Sans IG 小計
  Col 8: 總計 當月值
  Col 9: 總計 累計前期
  Col 10: 總計 (Grand Total YTD)

161B 同上 + Col 11: 商業庫存 (Stock au commerce)

8月合併表欄位:
  Col 0: 部門
  Cols 1-4: 161A (AOP, IGP, Sans IG, Total)
  Cols 5-8: 161B (AOP, IGP, Sans IG, Total)
  Col 9: Stock au commerce
"""

import pandas as pd
import numpy as np
import re
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. 設定檔案路徑
# ============================================================================

# 請依據你的檔案實際路徑修改此處
DATA_DIR = "/raw_data"

FILES = {
    "2019-2020": os.path.join(DATA_DIR, "Campagne-2019-2020.xls"),
    "2020-2021": os.path.join(DATA_DIR, "Campagne-2020-2021.xls"),
    "2021-2022": os.path.join(DATA_DIR, "Campagne-2021-2022.xls"),
    "2022-2023": os.path.join(DATA_DIR, "Etats_161_DATADOUANE_Campagne_2022-2023_0.xlsx"),
    "2023-2024": os.path.join(DATA_DIR, "Etats_161_DATADOUANE_Campagne_2023-2024.xlsx"),
    "2024-2025": os.path.join(DATA_DIR, "Etats_161_DATADOUANE_Campagne_2024-2025.xlsx"),
}

OUTPUT_DIR = DATA_DIR

# ============================================================================
# 2. 月份對照表 (法文月份 → 數字)
# ============================================================================

MONTH_MAP = {
    'aout': 8, 'août': 8,
    'sept': 9, 'septembre': 9,
    'oct': 10, 'octobre': 10,
    'nov': 11, 'novembre': 11,
    'dec': 12, 'déc': 12, 'décembre': 12,
    'janv': 1, 'janvier': 1,
    'fev': 2, 'fév': 2, 'février': 2, 'fevrier': 2,
    'mars': 3,
    'avril': 4, 'avr': 4,
    'mai': 5,
    'juin': 6,
    'juillet': 7, 'juil': 7,
}

def parse_month(sheet_name: str) -> int:
    """從 sheet 名稱提取月份數字"""
    name = sheet_name.lower().strip()
    for key, val in sorted(MONTH_MAP.items(), key=lambda x: -len(x[0])):
        if key in name:
            return val
    return 0

def parse_report_type(sheet_name: str) -> str:
    """從 sheet 名稱判斷報表類型: 161A, 161B, or combined"""
    name = sheet_name.lower()
    if '161a' in name.replace(' ', '') and '161b' in name.replace(' ', ''):
        return 'combined'
    elif '161b' in name.replace(' ', ''):
        return '161B'
    elif '161a' in name.replace(' ', ''):
        return '161A'
    # 新版 XLSX 命名: "Etat 161A ...", "Etat 161B ..."
    if 'etat' in name:
        if '161a' in name:
            return '161A'
        elif '161b' in name:
            return '161B'
    return 'unknown'

def extract_dept_code(dept_str: str) -> str:
    """從部門名稱提取部門代碼, e.g., 'O1 AIN' → '01', '13 BOUCHES-DU-RHONE' → '13'"""
    if pd.isna(dept_str):
        return ''
    s = str(dept_str).strip()
    # 替換 O → 0 (常見的零/O混用)
    match = re.match(r'^[O0]?(\d{1,2})\b', s)
    if match:
        return match.group(1).zfill(2)
    return ''


# ============================================================================
# 3. 核心解析函數
# ============================================================================

def find_data_start(df: pd.DataFrame) -> int:
    """找到資料起始行 (第一個部門代碼出現的行)"""
    for i in range(len(df)):
        cell = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
        if re.match(r'^[O0]?\d{1,2}\s+[A-Z]', cell):
            return i
    return -1

def parse_sheet_standard(df: pd.DataFrame, campagne: str, month: int,
                         report_type: str) -> list[dict]:
    """
    解析標準的 161A 或 161B 月報表 (9月-7月)
    
    161A 有 11 欄 (dept + 10 data cols)
    161B 有 12 欄 (dept + 10 data cols + stock)
    """
    start = find_data_start(df)
    if start < 0:
        return []
    
    records = []
    for i in range(start, len(df)):
        cell = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
        dept_code = extract_dept_code(cell)
        if not dept_code:
            continue
        
        row_data = df.iloc[i].tolist()
        dept_name = str(row_data[0]).strip()
        
        rec = {
            'campagne': campagne,
            'month': month,
            'report_type': report_type,
            'dept_code': dept_code,
            'dept_name': dept_name,
        }
        
        # 提取數值, 安全轉換
        def safe_num(idx):
            if idx < len(row_data) and pd.notna(row_data[idx]):
                try:
                    return float(row_data[idx])
                except (ValueError, TypeError):
                    return 0.0
            return 0.0
        
        if report_type in ('161A', '161B'):
            rec['aop_month'] = safe_num(1)
            rec['igp_month'] = safe_num(2)
            rec['ig_anterieurs'] = safe_num(3)
            rec['ig_total'] = safe_num(4)
            rec['sans_ig_month'] = safe_num(5)
            rec['sans_ig_anterieurs'] = safe_num(6)
            rec['sans_ig_total'] = safe_num(7)
            rec['total_month'] = safe_num(8)
            rec['total_anterieurs'] = safe_num(9)
            rec['grand_total'] = safe_num(10)
            
            if report_type == '161B':
                rec['stock_commerce'] = safe_num(11)
        
        records.append(rec)
    
    return records

def parse_sheet_combined(df: pd.DataFrame, campagne: str) -> list[dict]:
    """
    解析 8 月合併表 (161A + 161B 並排)
    
    Col 0: Département
    Cols 1-4: 161A (AOP, IGP, Sans IG, Total)
    Cols 5-8: 161B (AOP, IGP, Sans IG, Total)
    Col 9: Stock au commerce
    """
    start = find_data_start(df)
    if start < 0:
        return []
    
    records = []
    for i in range(start, len(df)):
        cell = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
        dept_code = extract_dept_code(cell)
        if not dept_code:
            continue
        
        row_data = df.iloc[i].tolist()
        dept_name = str(row_data[0]).strip()
        
        def safe_num(idx):
            if idx < len(row_data) and pd.notna(row_data[idx]):
                try:
                    return float(row_data[idx])
                except (ValueError, TypeError):
                    return 0.0
            return 0.0
        
        # 161A 記錄 (8月是第一個月, 沒有 antérieurs)
        rec_a = {
            'campagne': campagne,
            'month': 8,
            'report_type': '161A',
            'dept_code': dept_code,
            'dept_name': dept_name,
            'aop_month': safe_num(1),
            'igp_month': safe_num(2),
            'ig_anterieurs': 0.0,
            'ig_total': safe_num(1) + safe_num(2),
            'sans_ig_month': safe_num(3),
            'sans_ig_anterieurs': 0.0,
            'sans_ig_total': safe_num(3),
            'total_month': safe_num(4),
            'total_anterieurs': 0.0,
            'grand_total': safe_num(4),
        }
        
        # 161B 記錄
        rec_b = {
            'campagne': campagne,
            'month': 8,
            'report_type': '161B',
            'dept_code': dept_code,
            'dept_name': dept_name,
            'aop_month': safe_num(5),
            'igp_month': safe_num(6),
            'ig_anterieurs': 0.0,
            'ig_total': safe_num(5) + safe_num(6),
            'sans_ig_month': safe_num(7),
            'sans_ig_anterieurs': 0.0,
            'sans_ig_total': safe_num(7),
            'total_month': safe_num(8),
            'total_anterieurs': 0.0,
            'grand_total': safe_num(8),
            'stock_commerce': safe_num(9),
        }
        
        records.append(rec_a)
        records.append(rec_b)
    
    return records


# ============================================================================
# 4. 解析所有檔案
# ============================================================================

def parse_all_files() -> pd.DataFrame:
    """解析所有 campagne 檔案, 回傳統一的 DataFrame"""
    all_records = []
    
    for campagne, filepath in FILES.items():
        print(f"\n📂 解析: {campagne} ({os.path.basename(filepath)})")
        
        engine = 'xlrd' if filepath.endswith('.xls') else 'openpyxl'
        xls = pd.ExcelFile(filepath, engine=engine)
        
        for sheet_name in xls.sheet_names:
            report_type = parse_report_type(sheet_name)
            month = parse_month(sheet_name)
            
            if report_type == 'unknown' or month == 0:
                print(f"  ⚠️ 跳過無法識別的 sheet: '{sheet_name}'")
                continue
            
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            
            if report_type == 'combined':
                records = parse_sheet_combined(df, campagne)
            else:
                records = parse_sheet_standard(df, campagne, month, report_type)
            
            if records:
                print(f"  ✅ {sheet_name}: {report_type} Month={month} → {len(records)} 筆")
            else:
                print(f"  ⚠️ {sheet_name}: 未找到資料行")
            
            all_records.extend(records)
    
    df_all = pd.DataFrame(all_records)
    
    # 將 month 轉為 campagne 內的月序 (8月=1, 9月=2, ..., 7月=12)
    df_all['month_order'] = df_all['month'].apply(
        lambda m: m - 7 if m >= 8 else m + 5
    )
    
    # 計算日曆年月 (用於時間序列)
    def calc_calendar_year(row):
        camp_start = int(row['campagne'].split('-')[0])
        return camp_start if row['month'] >= 8 else camp_start + 1
    
    df_all['calendar_year'] = df_all.apply(calc_calendar_year, axis=1)
    df_all['calendar_ym'] = pd.to_datetime(
        df_all['calendar_year'].astype(str) + '-' + df_all['month'].astype(str).str.zfill(2) + '-01'
    )
    
    return df_all


# ============================================================================
# 5. 執行解析
# ============================================================================

print("=" * 60)
print("開始解析法國海關葡萄酒資料")
print("=" * 60)

df = parse_all_files()

print(f"\n{'=' * 60}")
print(f"解析完成! 總共 {len(df):,} 筆記錄")
print(f"Campagnes: {sorted(df['campagne'].unique())}")
print(f"Report types: {df['report_type'].unique()}")
print(f"Départements: {df['dept_code'].nunique()} 個")
print(f"月份範圍: {df['calendar_ym'].min()} ~ {df['calendar_ym'].max()}")


# ============================================================================
# 6. Provence 產區篩選
# ============================================================================

PROVENCE_DEPTS = ['13', '83']  # Bouches-du-Rhône, Var

df_provence = df[df['dept_code'].isin(PROVENCE_DEPTS)].copy()
print(f"\n🍷 Provence 產區 (13 + 83): {len(df_provence):,} 筆記錄")

# 也加入 Vaucluse (84) 作為參考 (Côtes du Rhône 也在此)
df_prov_extended = df[df['dept_code'].isin(['13', '83', '84'])].copy()


# ============================================================================
# 7. 建構分析用表
# ============================================================================

# 7a. 年度出莊量 (從每年 7 月的 grand_total 取得 = 全年累計)
df_annual_sortie = (
    df[(df['report_type'] == '161A') & (df['month'] == 7)]
    .groupby(['campagne', 'dept_code', 'dept_name'])
    ['grand_total']
    .sum()
    .reset_index()
    .rename(columns={'grand_total': 'annual_sortie_hl'})
)

print("\n📊 年度出莊量 (161A, 7月 YTD) - Provence")
prov_annual = df_annual_sortie[
    df_annual_sortie['dept_code'].isin(PROVENCE_DEPTS)
].sort_values(['dept_code', 'campagne'])
print(prov_annual.to_string(index=False))

# 7b. 月度出莊量 (取每月的 total_month 欄位)
df_monthly_sortie = (
    df[df['report_type'] == '161A']
    .groupby(['campagne', 'month', 'month_order', 'calendar_ym', 'dept_code'])
    ['total_month']
    .sum()
    .reset_index()
    .rename(columns={'total_month': 'monthly_sortie_hl'})
)

# 7c. 商業庫存 (161B 的 stock_commerce)
df_stock = (
    df[df['report_type'] == '161B']
    .groupby(['campagne', 'month', 'calendar_ym', 'dept_code'])
    ['stock_commerce']
    .sum()
    .reset_index()
)

# 7d. 流通稅申報量 (161B)
df_circ = (
    df[(df['report_type'] == '161B') & (df['month'] == 7)]
    .groupby(['campagne', 'dept_code'])
    ['grand_total']
    .sum()
    .reset_index()
    .rename(columns={'grand_total': 'annual_circulation_hl'})
)


# ============================================================================
# 8. 匯出統一 CSV
# ============================================================================

# 8a. 完整原始資料
csv_raw = os.path.join(OUTPUT_DIR, "wine_data_all_raw.csv")
df.to_csv(csv_raw, index=False, encoding='utf-8-sig')
print(f"\n💾 完整原始資料已匯出: {csv_raw}")

# 8b. Provence 月度分析表
csv_prov = os.path.join(OUTPUT_DIR, "wine_provence_monthly.csv")
df_prov_monthly = df_monthly_sortie[
    df_monthly_sortie['dept_code'].isin(PROVENCE_DEPTS)
].sort_values(['dept_code', 'calendar_ym'])
df_prov_monthly.to_csv(csv_prov, index=False, encoding='utf-8-sig')
print(f"💾 Provence 月度出莊量: {csv_prov}")

# 8c. 年度彙總表
csv_annual = os.path.join(OUTPUT_DIR, "wine_annual_summary.csv")
df_annual_sortie.to_csv(csv_annual, index=False, encoding='utf-8-sig')
print(f"💾 年度出莊量彙總: {csv_annual}")

# 8d. 庫存資料
csv_stock = os.path.join(OUTPUT_DIR, "wine_stock_commerce.csv")
df_stock_prov = df_stock[df_stock['dept_code'].isin(PROVENCE_DEPTS)]
df_stock_prov.to_csv(csv_stock, index=False, encoding='utf-8-sig')
print(f"💾 Provence 商業庫存: {csv_stock}")


# ============================================================================
# 9. Provence 分析摘要
# ============================================================================

print("\n" + "=" * 60)
print("🍷 PROVENCE 產區分析摘要")
print("=" * 60)

# 年度出莊量趨勢
print("\n【年度出莊量 (hl) — 161A Sorties des chais】")
pivot_annual = prov_annual.pivot(
    index='campagne', columns='dept_code', values='annual_sortie_hl'
)
if '13' in pivot_annual.columns and '83' in pivot_annual.columns:
    pivot_annual['Provence_total'] = pivot_annual['13'] + pivot_annual['83']
    pivot_annual.columns = ['Bouches-du-Rhône (13)', 'Var (83)', 'Provence Total']
    print(pivot_annual.to_string())
    
    # 年增率
    print("\n【年增率 (%)】")
    pct = pivot_annual.pct_change() * 100
    print(pct.round(1).to_string())

# 月度季節性分析
print("\n\n【月度季節性 — Var (83) 平均出莊量 (hl)】")
var_monthly = df_monthly_sortie[df_monthly_sortie['dept_code'] == '83']
month_names = {8:'Août',9:'Sept',10:'Oct',11:'Nov',12:'Déc',
               1:'Janv',2:'Fév',3:'Mars',4:'Avr',5:'Mai',6:'Juin',7:'Juil'}
seasonal = var_monthly.groupby('month')['monthly_sortie_hl'].mean()
seasonal.index = seasonal.index.map(lambda m: f"{m:02d} {month_names.get(m,'')}")
print(seasonal.round(0).to_string())

# AOP vs IGP vs Sans IG 結構
print("\n\n【出莊量結構 — Var (83), 按類別】")
var_161a = df[(df['report_type'] == '161A') & (df['dept_code'] == '83') & (df['month'] == 7)]
for _, row in var_161a.iterrows():
    aop_pct = row['ig_total'] / row['grand_total'] * 100 if row['grand_total'] > 0 else 0
    sans_pct = row['sans_ig_total'] / row['grand_total'] * 100 if row['grand_total'] > 0 else 0
    print(f"  {row['campagne']}: IG(AOP+IGP)={row['ig_total']:,.0f} ({aop_pct:.1f}%) | "
          f"Sans IG={row['sans_ig_total']:,.0f} ({sans_pct:.1f}%) | "
          f"Total={row['grand_total']:,.0f}")

# 庫存趨勢
print("\n\n【商業庫存 (hl) — Stock au commerce, 每年 7 月底】")
stock_july = df_stock[
    (df_stock['dept_code'].isin(PROVENCE_DEPTS)) & 
    (df_stock['month'] == 7)
].pivot_table(index='campagne', columns='dept_code', values='stock_commerce', aggfunc='sum')
if not stock_july.empty:
    stock_july.columns = ['Bouches-du-Rhône (13)', 'Var (83)']
    print(stock_july.to_string())

print("\n\n✅ 分析完成! 所有 CSV 已匯出至:", OUTPUT_DIR)
print("你可以用這些 CSV 在 IDE 中進一步分析或視覺化。")
