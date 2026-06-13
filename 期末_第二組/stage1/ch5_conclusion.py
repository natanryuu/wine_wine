"""
第 5 章：結論彙整
==================
產出：
  tables/ch5_key_findings.csv  — Stage 1 報告核心數字一覽（每章重點 stat）

把前 4 章的關鍵 finding 整合成一張供報告引用的彙總表。
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

from stage1._common import (
    DATA_DIR, TBL_DIR, save_table,
    cagr, linear_trend, welch_t, mann_whitney, cohen_d,
)


def compute_findings():
    rows = []

    # ============================================================
    # Ch.1 — 全球貿易
    # ============================================================
    un = pd.read_csv(os.path.join(DATA_DIR, 'un_comtrade_wine_clean.csv'))
    un['country'] = un['country'].replace({'United States': 'USA'})
    fr = un[(un['country'] == 'France') &
            (un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled')]
    fr_19 = fr[fr['year'] == 2019].iloc[0]
    fr_24 = fr[fr['year'] == 2024].iloc[0]
    fr_price_19 = (fr_19['trade_usd'] / fr_19['volume_litres']) * 0.75
    fr_price_24 = (fr_24['trade_usd'] / fr_24['volume_litres']) * 0.75

    rows.append(['Ch.1', '法國 2024 出口均價', f'${fr_price_24:.2f}/瓶 750ml',
                 'UN Comtrade Still_Bottled 出口'])
    rows.append(['Ch.1', '法國均價 CAGR (2019-2024)',
                 f'+{cagr(fr_price_19, fr_price_24, 5)*100:.1f}%/年',
                 '驗證 premiumization 趨勢'])
    rows.append(['Ch.1', '法國出口量 CAGR',
                 f'{cagr(fr_19["volume_litres"], fr_24["volume_litres"], 5)*100:.1f}%/年',
                 '量跌'])
    rows.append(['Ch.1', '法國出口值 CAGR',
                 f'+{cagr(fr_19["trade_usd"], fr_24["trade_usd"], 5)*100:.1f}%/年',
                 '值穩'])

    glb_24 = un[(un['flow'] == 'Export') &
                (un['commodity_short'] == 'Still_Bottled') &
                (un['year'] == 2024)]
    glb_price = (glb_24['trade_usd'].sum() / glb_24['volume_litres'].sum()) * 0.75
    rows.append(['Ch.1', '法國 vs 全球均價溢價', f'{fr_price_24/glb_price:.2f}×',
                 'France ÷ 全球加權均價'])

    # Welch's t
    agg = (un[(un['flow'] == 'Export') &
              (un['commodity_short'] == 'Still_Bottled')]
           .groupby(['year', 'country'])
           .agg(trade=('trade_usd', 'sum'), vol=('volume_litres', 'sum'))
           .reset_index())
    agg = agg[agg['vol'] > 0]
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75
    agg = agg[np.isfinite(agg['price'])]
    fr_prices = agg[agg['country'] == 'France']['price']
    other_targets = ['Italy', 'Spain', 'Chile', 'Australia', 'South Africa',
                     'Argentina', 'USA']
    other_prices = agg[agg['country'].isin(other_targets)]['price']
    w = welch_t(fr_prices, other_prices)
    rows.append(['Ch.1', '法國均價 vs 其他 7 國 Welch t-test',
                 f't={w["t"]:.2f}, p={w["p"]:.2e}{w["sig"]}',
                 '法國均價顯著高於對照組'])

    # ============================================================
    # Ch.2 — Rosé / Provence
    # ============================================================
    rose = pd.read_csv(os.path.join(DATA_DIR, 'rose_wines_dataset.csv'))
    fr_region = pd.read_csv(os.path.join(DATA_DIR, 'france_rose_by_region.csv'))
    pt = pd.read_csv(os.path.join(DATA_DIR, 'rose_price_tier_by_country.csv'))

    prov = fr_region[fr_region['province'] == 'Provence'].iloc[0]
    rows.append(['Ch.2', 'Provence Rosé 樣本數', f'{int(prov["wine_count"])} 支',
                 'Wine Enthusiast'])
    rows.append(['Ch.2', 'Provence 平均評分', f'{prov["avg_rating"]:.2f} 分',
                 '法國 11 產區之冠（與香檳並列）'])
    rows.append(['Ch.2', 'Provence 平均價格', f'${prov["avg_price"]:.2f}',
                 '中位 $19'])

    pt_idx = pt[pt['price_tier'].isin(['under_10', '10_15', '15_20', '20_30',
                                        '30_50', '50_100', '100_plus'])].set_index('price_tier')
    fr_total = pt_idx['France'].sum()
    fr_30plus = pt_idx['France'].loc[['30_50', '50_100', '100_plus']].sum() / fr_total * 100
    rows.append(['Ch.2', '法國 Rosé $30+ 高端帶占比', f'{fr_30plus:.1f}%',
                 '其他國家平均不到 10%'])

    contingency = pd.DataFrame({
        '法國': pt_idx['France'].values,
        '非法國': pt_idx[[c for c in pt_idx.columns if c not in ['France', 'All']]].sum(axis=1).values,
    })
    chi2, p, dof, _ = stats.chi2_contingency(contingency)
    rows.append(['Ch.2', '法國 vs 非法國 價格帶 χ² 檢定',
                 f'χ²={chi2:.1f}, p={p:.2e}',
                 '分布顯著不同'])

    # Provence vs 非 Provence 評分
    prov_pts = rose[rose['is_provence'] == 1]['points'].dropna()
    other_pts = rose[rose['is_provence'] == 0]['points'].dropna()
    mw = mann_whitney(prov_pts, other_pts)
    d = cohen_d(prov_pts, other_pts)
    rows.append(['Ch.2', 'Provence vs 非 Provence 評分',
                 f'中位 {int(mw["median_a"])} vs {int(mw["median_b"])}, '
                 f"d={d:.2f}, p={mw['p']:.2e}",
                 '靠品質而非價格差異化'])

    # ============================================================
    # Ch.3 — 法國產區供需
    # ============================================================
    panel = pd.read_csv(os.path.join(DATA_DIR, 'wine_supply_demand_panel.csv'))
    var_24 = panel[(panel['dept_code'] == 83) &
                    (panel['campagne'] == '2024-2025')].iloc[0]
    bdx_24 = panel[(panel['dept_code'] == 33) &
                    (panel['campagne'] == '2024-2025')].iloc[0]
    rows.append(['Ch.3', 'Var (83) 2024-25 庫存周轉率',
                 f'{var_24["stock_turnover_months"]:.1f} 月',
                 '5 大產區最快'])
    rows.append(['Ch.3', 'Bordeaux (33) 2024-25 庫存周轉率',
                 f'{bdx_24["stock_turnover_months"]:.1f} 月',
                 '結構性過剩'])

    var_panel = panel[panel['dept_code'] == 83].sort_values('campagne')
    var_panel = var_panel[var_panel['annual_sortie_hl'] > 0]
    var_sortie_cagr = cagr(var_panel['annual_sortie_hl'].iloc[0],
                            var_panel['annual_sortie_hl'].iloc[-1],
                            len(var_panel) - 1) * 100
    rows.append(['Ch.3', 'Var 出莊量 CAGR (6 年)', f'+{var_sortie_cagr:.1f}%/年',
                 '需求拉動型市場'])

    # Sans IG 趨勢
    raw = pd.read_csv(os.path.join(DATA_DIR, 'wine_data_all_raw.csv'))
    sub = raw[(raw['dept_code'] == 83) &
              (raw['month'] == 7) &
              (raw['report_type'] == '161A')].sort_values('campagne')
    sub['sans_ig_pct'] = sub['sans_ig_total'] / (sub['ig_total'] + sub['sans_ig_total']) * 100
    trend = linear_trend(np.arange(len(sub)), sub['sans_ig_pct'].values)
    rows.append(['Ch.3', 'Var Sans IG 占比變遷',
                 f'{sub["sans_ig_pct"].iloc[0]:.1f}% → {sub["sans_ig_pct"].iloc[-1]:.1f}%',
                 f'年增 +{trend["slope"]:.2f}%, R²={trend["r2"]:.2f}'])

    # 配對 t (Var vs Bordeaux)
    pair = panel[panel['dept_code'].isin([83, 33])].pivot(
        index='campagne', columns='dept_code', values='stock_turnover_months').dropna()
    t, p = stats.ttest_rel(pair[83].values, pair[33].values)
    rows.append(['Ch.3', 'Var vs Bordeaux 周轉率配對 t',
                 f't={t:.2f}, p={p:.2e}', '差距顯著'])

    # ============================================================
    # Ch.4 — 整合策略
    # ============================================================
    rows.append(['Ch.4', '三層論證', 'global premium → Provence 品質 → 海關驗證',
                 '三層數據支撐 premiumization 命題'])
    rows.append(['Ch.4', '進口市場優先排序矩陣',
                 '高價高量象限 = 優先進入 / 高價低量 = 利基培育',
                 '為 Stage 2 ML 排序模型奠基'])

    out = pd.DataFrame(rows, columns=['章節', '指標', '數字', '備註'])
    return out


def run():
    print('📋 Ch.5 — 結論彙整')
    findings = compute_findings()
    save_table(findings.set_index('章節'), 'ch5_key_findings')
    print('  ✅ Ch.5 done')


if __name__ == '__main__':
    run()
