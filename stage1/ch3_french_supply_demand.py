"""
第 3 章：法國產區供需結構分析
=============================
產出：
  figures/fig3_1_quadrant.png            — 四象限定位圖（CAGR × CV）
  figures/fig3_2_turnover_compare.png    — 5 產區庫存周轉率
  figures/fig3_3_var_supply_demand.png   — Var 供需平衡（柱+折線）
  figures/fig3_4_var_ig_structure.png    — Var IG vs Sans IG 結構變遷
  figures/fig3_5_seasonal_covid.png      — 月度季節性 + COVID 前後
  tables/ch3_paired_t.csv                — Var vs Bordeaux 周轉率配對 t
  tables/ch3_sans_ig_trend.csv           — Sans IG 線性趨勢回歸
  tables/ch3_descriptive_stats.csv       — 描述性統計 + 常態檢定 + Pearson 相關
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from stage1._common import (
    DATA_DIR, PALETTE, get_color, dept_label,
    style_axes, add_source_note, save_fig, save_table,
    cagr, linear_trend, mann_whitney, stars,
)

PANEL_CSV = os.path.join(DATA_DIR, 'wine_supply_demand_panel.csv')
COMPARE_CSV = os.path.join(DATA_DIR, 'wine_region_comparison.csv')
PROVENCE_CSV = os.path.join(DATA_DIR, 'wine_provence_supply_demand.csv')
MONTHLY_CSV = os.path.join(DATA_DIR, 'wine_provence_monthly.csv')
RAW_CSV = os.path.join(DATA_DIR, 'wine_data_all_raw.csv')

SRC_NOTE = '資料來源：法國海關 DGDDI Etats 161A/B'

# 比對的 5 個產區（dept_code）
COMPARE_DEPTS = [83, 13, 33, 34, 84]  # Var, BdR, Bordeaux, Languedoc, Vaucluse
DEPT_PALETTE = {
    83: PALETTE['Var'],
    13: PALETTE['BdR'],
    33: PALETTE['Bordeaux'],
    34: PALETTE['Languedoc'],
    84: PALETTE['Vaucluse'],
}


def load_panel():
    df = pd.read_csv(PANEL_CSV)
    return df


# ============================================================
# Fig 3.1 — 四象限定位圖（CAGR × CV）
# ============================================================
def fig3_1_quadrant(panel):
    # 鎖定主要產酒部門
    target_depts = [83, 13, 33, 34, 84, 11, 30, 66, 51, 21]
    df = panel[panel['dept_code'].isin(target_depts)].copy()

    # 計算每個 dept 的 sortie CAGR (6年) + CV (波動性)
    rows = []
    for dept in target_depts:
        sub = df[df['dept_code'] == dept].sort_values('campagne')
        sub = sub[sub['annual_sortie_hl'].notna() & (sub['annual_sortie_hl'] > 0)]
        if len(sub) < 3:
            continue
        first = sub['annual_sortie_hl'].iloc[0]
        last = sub['annual_sortie_hl'].iloc[-1]
        n_periods = len(sub) - 1
        c = cagr(first, last, n_periods)
        cv = sub['annual_sortie_hl'].std() / sub['annual_sortie_hl'].mean()
        rows.append({
            'dept': dept,
            'cagr_pct': c * 100,
            'cv_pct': cv * 100,
            'mean_sortie': sub['annual_sortie_hl'].mean(),
        })
    pos = pd.DataFrame(rows)

    # 中位數十字線
    cv_mid = pos['cv_pct'].median()
    cagr_mid = pos['cagr_pct'].median()

    fig, ax = plt.subplots(figsize=(11, 7))
    style_axes(ax,
               title='法國主要產酒區四象限定位（出莊量 CAGR × 波動性）',
               xlabel='波動性 CV (%)', ylabel='年複合成長率 CAGR (%)')

    # 十字分隔線
    ax.axvline(cv_mid, color=PALETTE['text2'], linestyle='--', linewidth=0.9, alpha=0.7)
    ax.axhline(cagr_mid, color=PALETTE['text2'], linestyle='--', linewidth=0.9, alpha=0.7)
    ax.axhline(0, color=PALETTE['text2'], linestyle='-', linewidth=0.6, alpha=0.4)

    sizes = (pos['mean_sortie'] / pos['mean_sortie'].max()) * 1800 + 150
    for i, row in pos.reset_index(drop=True).iterrows():
        d = int(row['dept'])
        c = DEPT_PALETTE.get(d, PALETTE['text2'])
        ax.scatter(row['cv_pct'], row['cagr_pct'], s=sizes[i],
                   color=c, alpha=0.65, edgecolor=c, linewidth=2.2)
        ax.annotate(dept_label(d),
                    xy=(row['cv_pct'], row['cagr_pct']),
                    ha='center', va='center',
                    fontsize=9.5, fontweight='bold',
                    color=PALETTE['text'])

    # 象限文字（取軸範圍）
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    quad_meta = [
        # (cx_frac, cy_frac, label, color)
        (0.18, 0.92, '穩定成長\n（低波動 + 高成長）', PALETTE['Var']),
        (0.82, 0.92, '高速擴張\n（高波動 + 高成長）', PALETTE['Spain']),
        (0.18, 0.08, '守成型\n（低波動 + 低成長）', PALETTE['Languedoc']),
        (0.82, 0.08, '風險區\n（高波動 + 低成長）', PALETTE['Bordeaux']),
    ]
    for fx, fy, label, color in quad_meta:
        x_pos = xlim[0] + (xlim[1] - xlim[0]) * fx
        y_pos = ylim[0] + (ylim[1] - ylim[0]) * fy
        ax.text(x_pos, y_pos, label,
                ha='center', va='center',
                fontsize=10, color=color,
                fontweight='bold', alpha=0.55)

    # 圓圈大小說明 — 放在 figure 邊界，剛好在資料來源上方一點
    fig.text(0.99, 0.04, '圓圈大小 = 平均年出莊量',
             ha='right', va='bottom',
             fontsize=9, color=PALETTE['text2'], style='italic')

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig3_1_quadrant')


# ============================================================
# Fig 3.2 — 5 產區庫存周轉率折線
# ============================================================
def fig3_2_turnover_compare(panel):
    df = panel[panel['dept_code'].isin(COMPARE_DEPTS)].copy()
    df = df[df['stock_turnover_months'].notna()]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    style_axes(ax,
               title='5 大產區庫存周轉率比較（月，越低去化越快）',
               xlabel='Campagne', ylabel='庫存周轉率（月）')

    last_camp = sorted(df['campagne'].unique())[-1]
    for d in COMPARE_DEPTS:
        sub = df[df['dept_code'] == d].sort_values('campagne')
        is_var = d == 83
        ax.plot(sub['campagne'], sub['stock_turnover_months'],
                marker='o', markersize=6,
                linewidth=3 if is_var else 1.8,
                color=DEPT_PALETTE[d],
                alpha=1.0 if is_var else 0.85,
                label=dept_label(d))
        # 標最後一年
        last_v = sub[sub['campagne'] == last_camp]['stock_turnover_months'].values
        if len(last_v):
            ax.annotate(f'{last_v[0]:.1f}',
                        xy=(last_camp, last_v[0]),
                        xytext=(6, 0), textcoords='offset points',
                        fontsize=9, color=DEPT_PALETTE[d],
                        fontweight='bold' if is_var else 'normal',
                        va='center')

    ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5),
              frameon=False, fontsize=10)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha='right')

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig3_2_turnover_compare')


# ============================================================
# Fig 3.3 — Var 供需平衡（柱+折線）
# ============================================================
def fig3_3_var_supply_demand(panel):
    df = panel[panel['dept_code'] == 83].sort_values('campagne').copy()

    fig, ax_l = plt.subplots(figsize=(11, 6.5))
    style_axes(ax_l,
               title='Var (83) 供需平衡：產量 vs 出莊量 vs 庫存',
               xlabel='Campagne', ylabel='產量 / 出莊量（百萬公升）')

    x_pos = np.arange(len(df))
    width = 0.36
    prod_m = df['prod_commercialisable'].values / 1e6
    sortie_m = df['annual_sortie_hl'].values / 1e6

    bars_p = ax_l.bar(x_pos - width / 2, prod_m, width,
                      color=PALETTE['Var'], alpha=0.8,
                      label='產量', edgecolor='white', linewidth=0.8)
    bars_s = ax_l.bar(x_pos + width / 2, sortie_m, width,
                      color=PALETTE['Spain'], alpha=0.85,
                      label='出莊量', edgecolor='white', linewidth=0.8)

    for b, v in zip(bars_p, prod_m):
        if not np.isnan(v):
            ax_l.text(b.get_x() + b.get_width() / 2, v + 0.05,
                      f'{v:.1f}', ha='center', va='bottom',
                      fontsize=8, color=PALETTE['Var'])
    for b, v in zip(bars_s, sortie_m):
        if not np.isnan(v):
            ax_l.text(b.get_x() + b.get_width() / 2, v + 0.05,
                      f'{v:.1f}', ha='center', va='bottom',
                      fontsize=8, color=PALETTE['Spain'])

    ax_l.set_xticks(x_pos)
    ax_l.set_xticklabels(df['campagne'].values, rotation=20, ha='right')

    # 右軸：庫存
    ax_r = ax_l.twinx()
    stock_m = df['stock_production_total'].values / 1e6
    ax_r.plot(x_pos, stock_m,
              marker='D', markersize=7,
              linewidth=2.5, color=PALETTE['Rose'],
              label='生產庫存')
    for x, v in zip(x_pos, stock_m):
        if not np.isnan(v):
            ax_r.annotate(f'{v:.2f}',
                          xy=(x, v), xytext=(0, 9),
                          textcoords='offset points',
                          fontsize=8.5, color=PALETTE['Rose'],
                          fontweight='bold', ha='center')
    ax_r.set_ylabel('生產庫存（百萬公升）', color=PALETTE['Rose'], fontsize=11)
    ax_r.tick_params(axis='y', colors=PALETTE['Rose'], labelsize=9)
    ax_r.spines['right'].set_color(PALETTE['Rose'])
    ax_r.spines['top'].set_visible(False)
    ax_r.grid(False)

    # 右軸從 0 起，避免窄範圍 auto-scale 誇大視覺變化
    stock_max = np.nanmax(stock_m) * 1.15
    ax_r.set_ylim(0, stock_max)

    # 合併 legend
    h1, l1 = ax_l.get_legend_handles_labels()
    h2, l2 = ax_r.get_legend_handles_labels()
    ax_l.legend(h1 + h2, l1 + l2, loc='upper left', frameon=False, fontsize=9)

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig3_3_var_supply_demand')


# ============================================================
# Fig 3.4 — Var IG vs Sans IG 結構變遷（堆疊面積）
# ============================================================
def fig3_4_var_ig_structure(panel_raw_path=RAW_CSV):
    df = pd.read_csv(panel_raw_path)
    sub = df[(df['dept_code'] == 83) &
             (df['month'] == 7) &
             (df['report_type'] == '161A')].copy()
    sub = sub.sort_values('campagne')

    sub['ig_pct'] = sub['ig_total'] / (sub['ig_total'] + sub['sans_ig_total']) * 100
    sub['sans_ig_pct'] = sub['sans_ig_total'] / (sub['ig_total'] + sub['sans_ig_total']) * 100

    fig, ax = plt.subplots(figsize=(11, 6))
    style_axes(ax,
               title='Var (83) 出莊結構變遷：IG vs Sans IG',
               xlabel='Campagne', ylabel='占比（%）')

    x_pos = np.arange(len(sub))
    ax.fill_between(x_pos, 0, sub['ig_pct'].values,
                    color=PALETTE['Var'], alpha=0.85, label='IG (AOP+IGP)')
    ax.fill_between(x_pos, sub['ig_pct'].values, 100,
                    color=PALETTE['Spain'], alpha=0.85, label='Sans IG')
    ax.set_ylim(80, 100)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(sub['campagne'].values, rotation=20, ha='right')

    # 標起終值
    for i, row in sub.reset_index(drop=True).iterrows():
        if i == 0 or i == len(sub) - 1:
            ax.annotate(f"IG {row['ig_pct']:.1f}%",
                        xy=(i, row['ig_pct'] - 1),
                        ha='center', va='top',
                        fontsize=10, color=PALETTE['text'], fontweight='bold')
            ax.annotate(f"Sans IG {row['sans_ig_pct']:.1f}%",
                        xy=(i, row['ig_pct'] + 0.5),
                        ha='center', va='bottom',
                        fontsize=10, color=PALETTE['text'], fontweight='bold')

    # 線性趨勢數字
    years_idx = np.arange(len(sub))
    trend = linear_trend(years_idx, sub['sans_ig_pct'].values)
    note = (f"Sans IG 線性趨勢：每年 +{trend['slope']:.2f}% "
            f"(R²={trend['r2']:.2f}, p={trend['p']:.3f}{trend['sig']})")
    ax.text(0.5, -0.20, note,
            transform=ax.transAxes,
            ha='center', va='top',
            fontsize=10, color=PALETTE['text'], style='italic')

    ax.legend(loc='upper right', frameon=False, fontsize=10)
    add_source_note(fig, SRC_NOTE)
    plt.tight_layout()
    save_fig(fig, 'fig3_4_var_ig_structure')


# ============================================================
# Fig 3.5 — 月度季節性 + COVID 前後
# ============================================================
def fig3_5_seasonal_covid():
    df = pd.read_csv(MONTHLY_CSV)
    # 鎖定 Provence 5 部門總和
    prov_depts = [83, 13, 84, 4, 6]
    df = df[df['dept_code'].isin(prov_depts)].copy()

    # 月平均（跨年取均）
    monthly_avg = df.groupby('month')['monthly_sortie_hl'].mean()
    # 法文月份排序：8,9,10,11,12,1,2,3,4,5,6,7
    month_order = [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7]
    monthly_avg = monthly_avg.reindex(month_order)

    month_labels_zh = {
        1: '一月', 2: '二月', 3: '三月', 4: '四月', 5: '五月', 6: '六月',
        7: '七月', 8: '八月', 9: '九月', 10: '十月', 11: '十一月', 12: '十二月',
    }

    fig, ax = plt.subplots(figsize=(11, 6))
    style_axes(ax,
               title='Provence 5 部門月度平均出莊量 + COVID 前後比較',
               xlabel='月份', ylabel='平均出莊量（公升，跨年平均）')

    # 旺季月份（1-6 月）以 Rose 突顯
    bars = []
    for m in month_order:
        is_peak = m in [1, 2, 3, 4, 5, 6]
        c = PALETTE['Rose'] if is_peak else PALETTE['text2']
        b = ax.bar(month_labels_zh[m], monthly_avg[m] / 1e3,
                   color=c, alpha=0.75 if is_peak else 0.5,
                   edgecolor='white', linewidth=0.8)
        bars.append(b)

    # 旺季註記
    ax.text(0.30, 0.95, '↑ 旺季（1–6 月）',
            transform=ax.transAxes,
            ha='center', va='top', fontsize=10,
            color=PALETTE['Rose'], fontweight='bold')

    plt.setp(ax.xaxis.get_majorticklabels(), rotation=20, ha='right')
    ax.set_ylabel('平均出莊量（千公升）')

    # COVID 比較：把 2020-2021 + 2021-2022 為 COVID，其他為非 COVID
    covid_camps = ['2020-2021', '2021-2022']
    covid_data = df[df['campagne'].isin(covid_camps)]['monthly_sortie_hl'].dropna().values
    non_covid_data = df[~df['campagne'].isin(covid_camps)]['monthly_sortie_hl'].dropna().values
    mw = mann_whitney(covid_data, non_covid_data)

    covid_note = (f'COVID（2020-22）vs 其他年: Mann-Whitney U={int(mw["U"])}, '
                  f'p={mw["p"]:.3f}{mw["sig"] or "（不顯著）"}')
    ax.text(0.5, -0.18, covid_note,
            transform=ax.transAxes,
            ha='center', va='top',
            fontsize=10, color=PALETTE['text'], style='italic')

    add_source_note(fig, SRC_NOTE)
    plt.tight_layout()
    save_fig(fig, 'fig3_5_seasonal_covid')


# ============================================================
# Table 3.1 — Var vs Bordeaux 周轉率配對 t
# ============================================================
def table3_1_paired_t(panel):
    sub = panel[panel['dept_code'].isin([83, 33])].copy()
    sub = sub[sub['stock_turnover_months'].notna()]
    pivot = sub.pivot(index='campagne', columns='dept_code',
                       values='stock_turnover_months')
    pivot = pivot.dropna()  # 只保留兩邊都有的年份

    var = pivot[83].values
    bdx = pivot[33].values
    diff = var - bdx

    t_stat, p_val = stats.ttest_rel(var, bdx)

    out = pd.DataFrame([{
        '檢定': 'Var vs Bordeaux 庫存周轉率配對 t',
        'n（年數）': len(pivot),
        'Var 平均（月）': round(np.mean(var), 2),
        'Bordeaux 平均（月）': round(np.mean(bdx), 2),
        '差距平均（月）': round(np.mean(diff), 2),
        't 值': round(t_stat, 3),
        'p 值': f"{p_val:.2e}",
        '顯著': stars(p_val),
    }])
    save_table(out.set_index('檢定'), 'ch3_paired_t')


# ============================================================
# Table 3.2 — Sans IG 線性趨勢回歸
# ============================================================
def table3_2_sans_ig_trend():
    df = pd.read_csv(RAW_CSV)
    sub = df[(df['dept_code'] == 83) &
             (df['month'] == 7) &
             (df['report_type'] == '161A')].sort_values('campagne').copy()
    sub['sans_ig_pct'] = sub['sans_ig_total'] / (sub['ig_total'] + sub['sans_ig_total']) * 100

    years_idx = np.arange(len(sub))
    res = linear_trend(years_idx, sub['sans_ig_pct'].values)

    out = pd.DataFrame([{
        '檢定': 'Var Sans IG % 線性趨勢',
        'n': len(sub),
        '起點 %': round(sub['sans_ig_pct'].iloc[0], 2),
        '終點 %': round(sub['sans_ig_pct'].iloc[-1], 2),
        '年增 (slope %)': round(res['slope'], 3),
        'R²': round(res['r2'], 3),
        'p 值': f"{res['p']:.2e}",
        '顯著': res['sig'],
    }])
    save_table(out.set_index('檢定'), 'ch3_sans_ig_trend')


# ============================================================
# Table 3.3 — 描述性統計 + 常態檢定 + Pearson 相關
# ============================================================
def table3_3_descriptive(panel):
    # 取 5 部門的關鍵變數做描述
    sub = panel[panel['dept_code'].isin(COMPARE_DEPTS)].copy()
    cols = {
        'prod_commercialisable': '可商業化產量',
        'annual_sortie_hl': '年出莊量',
        'stock_production_total': '生產庫存',
        'stock_turnover_months': '庫存周轉率',
    }

    rows = []
    for col, name in cols.items():
        s = sub[col].dropna()
        if len(s) < 3:
            continue
        # Shapiro-Wilk 常態檢定（n<5000 可用）
        if len(s) <= 5000:
            sw_stat, sw_p = stats.shapiro(s)
        else:
            sw_stat, sw_p = np.nan, np.nan
        rows.append({
            '變數': name,
            'n': len(s),
            'mean': round(s.mean(), 2),
            'std': round(s.std(), 2),
            'min': round(s.min(), 2),
            'median': round(s.median(), 2),
            'max': round(s.max(), 2),
            'Shapiro-Wilk W': round(sw_stat, 3) if not np.isnan(sw_stat) else '-',
            'Shapiro p': f"{sw_p:.2e}" if not np.isnan(sw_p) else '-',
            '常態': '✓' if (not np.isnan(sw_p) and sw_p > 0.05) else '✗',
        })
    desc = pd.DataFrame(rows).set_index('變數')
    save_table(desc, 'ch3_descriptive_stats')

    # Pearson 相關矩陣
    corr_df = sub[list(cols.keys())].dropna()
    corr = corr_df.corr(method='pearson').round(3)
    corr.index = [cols[c] for c in corr.index]
    corr.columns = [cols[c] for c in corr.columns]

    # 加 p-value 矩陣
    n_vars = len(cols)
    p_matrix = np.zeros((n_vars, n_vars))
    var_names = list(cols.values())
    arr = corr_df.values
    for i in range(n_vars):
        for j in range(n_vars):
            if i == j:
                p_matrix[i, j] = 0
            else:
                _, p = stats.pearsonr(arr[:, i], arr[:, j])
                p_matrix[i, j] = p
    # 把顯著符號蓋進相關矩陣
    corr_with_stars = corr.copy().astype(str)
    for i in range(n_vars):
        for j in range(n_vars):
            if i != j:
                s = stars(p_matrix[i, j])
                corr_with_stars.iat[i, j] = f'{corr.iat[i, j]:.3f}{s}'
    save_table(corr_with_stars, 'ch3_pearson_corr')


# ============================================================
# main
# ============================================================
def run():
    print('🇫🇷 Ch.3 — 法國產區供需結構分析')
    panel = load_panel()
    fig3_1_quadrant(panel)
    fig3_2_turnover_compare(panel)
    fig3_3_var_supply_demand(panel)
    fig3_4_var_ig_structure()
    fig3_5_seasonal_covid()
    table3_1_paired_t(panel)
    table3_2_sans_ig_trend()
    table3_3_descriptive(panel)
    print('  ✅ Ch.3 done')


if __name__ == '__main__':
    run()
