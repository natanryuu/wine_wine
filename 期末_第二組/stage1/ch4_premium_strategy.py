"""
第 4 章：Premiumization 策略整合
=================================
產出：
  figures/fig4_1_dashboard.png         — 三層論證 KPI 儀表板（3×3 卡片）
  figures/fig4_2_import_market.png     — 出口市場優先排序四象限矩陣
  tables/ch4_market_segments.csv       — 進口市場分類（高價高量等）
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from stage1._common import (
    DATA_DIR, PALETTE, country_label,
    style_axes, add_source_note, save_fig, save_table,
    cagr,
)

UN_CSV = os.path.join(DATA_DIR, 'un_comtrade_wine_clean.csv')
PANEL_CSV = os.path.join(DATA_DIR, 'wine_supply_demand_panel.csv')
RAW_CSV = os.path.join(DATA_DIR, 'wine_data_all_raw.csv')
FR_REGION_CSV = os.path.join(DATA_DIR, 'france_rose_by_region.csv')
PRICE_TIER_CSV = os.path.join(DATA_DIR, 'rose_price_tier_by_country.csv')


# ============================================================
# 4.1 — 三層論證 KPI 儀表板（3×3 卡片網格）
# ============================================================
def fig4_1_dashboard():
    # === 計算九個 KPI ===

    # 第 1 層：全球 Premiumization
    un = pd.read_csv(UN_CSV)
    un['country'] = un['country'].replace({'United States': 'USA'})
    fr = un[(un['country'] == 'France') &
            (un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled')].copy()
    fr_2019 = fr[fr['year'] == 2019]
    fr_2024 = fr[fr['year'] == 2024]
    price_2024 = (fr_2024['trade_usd'].sum() / fr_2024['volume_litres'].sum()) * 0.75
    price_2019 = (fr_2019['trade_usd'].sum() / fr_2019['volume_litres'].sum()) * 0.75
    price_cagr = cagr(price_2019, price_2024, 5) * 100

    # 法國 vs 全球均價
    glb = un[(un['flow'] == 'Export') &
             (un['commodity_short'] == 'Still_Bottled') &
             (un['year'] == 2024)]
    glb_price = (glb['trade_usd'].sum() / glb['volume_litres'].sum()) * 0.75
    premium_x = price_2024 / glb_price

    # 第 2 層：Provence rosé 品質
    fr_region = pd.read_csv(FR_REGION_CSV)
    prov = fr_region[fr_region['province'] == 'Provence'].iloc[0]

    # 法國 $30+ 高端帶占比
    pt = pd.read_csv(PRICE_TIER_CSV)
    pt_idx = pt[pt['price_tier'].isin(['under_10', '10_15', '15_20', '20_30',
                                        '30_50', '50_100', '100_plus'])].set_index('price_tier')
    fr_total = pt_idx['France'].sum()
    fr_30plus = pt_idx['France'].loc[['30_50', '50_100', '100_plus']].sum() / fr_total * 100

    # 第 3 層：海關供需
    panel = pd.read_csv(PANEL_CSV)
    var_2024 = panel[(panel['dept_code'] == 83) &
                      (panel['campagne'] == '2024-2025')].iloc[0]
    var_turnover = var_2024['stock_turnover_months']

    raw = pd.read_csv(RAW_CSV)
    sub = raw[(raw['dept_code'] == 83) &
              (raw['month'] == 7) &
              (raw['report_type'] == '161A')].sort_values('campagne')
    sans_ig_pct_first = (sub['sans_ig_total'].iloc[0] /
                         (sub['ig_total'].iloc[0] + sub['sans_ig_total'].iloc[0]) * 100)
    sans_ig_pct_last = (sub['sans_ig_total'].iloc[-1] /
                        (sub['ig_total'].iloc[-1] + sub['sans_ig_total'].iloc[-1]) * 100)

    # Var 出莊量 CAGR
    var_panel = panel[panel['dept_code'] == 83].sort_values('campagne')
    var_panel = var_panel[var_panel['annual_sortie_hl'] > 0]
    var_sortie_cagr = cagr(var_panel['annual_sortie_hl'].iloc[0],
                            var_panel['annual_sortie_hl'].iloc[-1],
                            len(var_panel) - 1) * 100

    # === 卡片內容 ===
    cards = [
        # Tier 1 — 全球 Premiumization
        ('全球趨勢', f'${price_2024:.2f}', '法國瓶裝出口均價（2024）',
         f'+{price_cagr:.1f}% CAGR', PALETTE['Global']),
        ('全球趨勢', f'{premium_x:.2f}×', '法國 vs 全球均價溢價',
         '高端化定位確立', PALETTE['Global']),
        ('全球趨勢', f'${price_2024 / price_2019 * 100 - 100:+.0f}%',
         '法國均價 6 年累積漲幅',
         '量跌但值與價皆漲', PALETTE['Global']),

        # Tier 2 — Provence rosé 品質
        ('Provence 品質', f'{prov["avg_rating"]:.1f} 分',
         'Wine Enthusiast 評分（n=954）', '法國產區之冠', PALETTE['Rose']),
        ('Provence 品質', f'${prov["avg_price"]:.0f}',
         'Provence rosé 平均價格', '中高端定位', PALETTE['Rose']),
        ('Provence 品質', f'{fr_30plus:.1f}%',
         '法國 rosé $30+ 高端帶占比', '其他國家平均不到 10%', PALETTE['Rose']),

        # Tier 3 — 海關供需
        ('供需驗證', f'{var_turnover:.1f} 月',
         'Var (83) 庫存周轉率', '5 大產區最快', PALETTE['Var']),
        ('供需驗證', f'+{var_sortie_cagr:.1f}%',
         'Var 出莊量 CAGR（6 年）', '需求拉動型市場', PALETTE['Var']),
        ('供需驗證', f'{sans_ig_pct_first:.1f}% → {sans_ig_pct_last:.1f}%',
         'Var Sans IG 占比（線性 R²=0.95）', '需關注的結構轉變', PALETTE['Var']),
    ]

    # === 繪圖：3 列 × 3 欄 KPI 卡片 ===
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(PALETTE['bg'])

    fig.suptitle('Provence Rosé Premiumization 三層論證儀表板',
                 fontsize=17, fontweight='bold', color=PALETTE['text'], y=0.97)
    fig.text(0.5, 0.92,
             '全球趨勢（資料層）→ Provence 品質（評鑑層）→ 海關供需（驗證層）',
             ha='center', fontsize=11, color=PALETTE['text2'], style='italic')

    # 三層左側標籤
    tier_labels = ['全球趨勢', 'Provence 品質', '供需驗證']
    tier_colors = [PALETTE['Global'], PALETTE['Rose'], PALETTE['Var']]
    for i, (label, color) in enumerate(zip(tier_labels, tier_colors)):
        # 對應 row：i=0 → row 2 (top), i=1 → row 1 (mid), i=2 → row 0 (bottom)
        y_center = 2.5 - i  # row top y position center
        fig.text(0.04, 0.78 - i * 0.27, label,
                 ha='center', va='center',
                 fontsize=12, fontweight='bold', color=color, rotation=90)

    # 9 張 KPI 卡片
    for idx, (tier, big_num, label, sub_text, color) in enumerate(cards):
        row = idx // 3  # 0=top, 1=mid, 2=bot
        col = idx % 3
        x0 = col + 0.07
        y0 = (2 - row) + 0.08
        w, h = 0.86, 0.84

        # 卡片背景
        card = Rectangle((x0, y0), w, h,
                          facecolor='white', edgecolor=color,
                          linewidth=1.6, alpha=0.95,
                          transform=ax.transData)
        ax.add_patch(card)

        # 大數字
        ax.text(x0 + w / 2, y0 + h * 0.62, big_num,
                ha='center', va='center',
                fontsize=24, fontweight='bold', color=color,
                transform=ax.transData)

        # 中間 label
        ax.text(x0 + w / 2, y0 + h * 0.30, label,
                ha='center', va='center',
                fontsize=10, color=PALETTE['text'],
                transform=ax.transData)

        # 底部 subtext
        ax.text(x0 + w / 2, y0 + h * 0.12, sub_text,
                ha='center', va='center',
                fontsize=9, color=PALETTE['text2'], style='italic',
                transform=ax.transData)

    add_source_note(fig, '資料來源：UN Comtrade / Wine Enthusiast / 法國海關 DGDDI')
    save_fig(fig, 'fig4_1_dashboard')


# ============================================================
# 4.2 — 出口市場優先排序四象限矩陣
# ============================================================
def fig4_2_import_market_matrix():
    un = pd.read_csv(UN_CSV)
    un['country'] = un['country'].replace({
        'United States': 'USA',
        'China, Hong Kong SAR': 'Hong Kong',
        'China, Macao SAR': 'Macao',
    })

    # 2024 進口（任何葡萄酒類別總和）
    df = un[(un['flow'] == 'Import') & (un['year'] == 2024)].copy()
    df = df[df['volume_litres'].notna() & (df['volume_litres'] > 0)]

    agg = df.groupby('country').agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg['unit_price'] = agg['trade'] / agg['vol']

    # 取 top 12 by trade_usd
    agg = agg.sort_values('trade', ascending=False).head(12).reset_index(drop=True)
    agg['trade_b'] = agg['trade'] / 1e9

    # 四象限分隔線（用 median 做切分）
    x_mid = agg['trade_b'].median()
    y_mid = agg['unit_price'].median()

    # 分類
    def classify(row):
        if row['trade_b'] >= x_mid and row['unit_price'] >= y_mid:
            return '高價高量'
        if row['trade_b'] >= x_mid and row['unit_price'] < y_mid:
            return '低價高量'
        if row['trade_b'] < x_mid and row['unit_price'] >= y_mid:
            return '高價低量'
        return '低價低量'
    agg['segment'] = agg.apply(classify, axis=1)

    # 為各 segment 上色
    seg_color = {
        '高價高量': PALETTE['Var'],
        '高價低量': PALETTE['Rose'],
        '低價高量': PALETTE['Spain'],
        '低價低量': PALETTE['text2'],
    }

    fig, ax = plt.subplots(figsize=(12, 7.5))
    style_axes(ax,
               title='2024 年葡萄酒進口市場優先排序矩陣（Top 12）',
               xlabel='進口總值（十億美元）',
               ylabel='進口均價（美元/公升）')

    ax.axvline(x_mid, color=PALETTE['text2'], linestyle='--', linewidth=0.9, alpha=0.7)
    ax.axhline(y_mid, color=PALETTE['text2'], linestyle='--', linewidth=0.9, alpha=0.7)

    sizes = (agg['vol'] / agg['vol'].max()) * 1800 + 150
    for i, row in agg.iterrows():
        c = seg_color[row['segment']]
        ax.scatter(row['trade_b'], row['unit_price'], s=sizes[i],
                   color=c, alpha=0.6, edgecolor=c, linewidth=2)
        ax.annotate(country_label(row['country']),
                    xy=(row['trade_b'], row['unit_price']),
                    ha='center', va='center',
                    fontsize=10, fontweight='bold',
                    color=PALETTE['text'])

    # 象限標籤（淡色，放四角）
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    quadrants = [
        (0.85, 0.92, '高價高量\n（優先進入）', PALETTE['Var']),
        (0.15, 0.92, '高價低量\n（利基/培育）', PALETTE['Rose']),
        (0.85, 0.08, '低價高量\n（量大但低價）', PALETTE['Spain']),
        (0.15, 0.08, '低價低量\n（觀望）', PALETTE['text2']),
    ]
    for fx, fy, label, color in quadrants:
        x_pos = xlim[0] + (xlim[1] - xlim[0]) * fx
        y_pos = ylim[0] + (ylim[1] - ylim[0]) * fy
        ax.text(x_pos, y_pos, label,
                ha='center', va='center',
                fontsize=10, color=color, fontweight='bold', alpha=0.5)

    fig.text(0.99, 0.04, '圓圈大小 = 進口量',
             ha='right', va='bottom',
             fontsize=9, color=PALETTE['text2'], style='italic')

    add_source_note(fig, '資料來源：UN Comtrade, HS 2204')
    save_fig(fig, 'fig4_2_import_market')

    # === Table 4.1：市場分類表 ===
    out = agg.copy()
    out['country_zh'] = out['country'].map(country_label)
    out = out[['country_zh', 'segment', 'trade_b', 'vol', 'unit_price']]
    out.columns = ['市場', '分類', '進口總值（十億 USD）', '進口量（公升）', '進口單價（USD/L）']
    out['進口總值（十億 USD）'] = out['進口總值（十億 USD）'].round(2)
    out['進口量（公升）'] = (out['進口量（公升）'] / 1e6).round(1)
    out.rename(columns={'進口量（公升）': '進口量（百萬公升）'}, inplace=True)
    out['進口單價（USD/L）'] = out['進口單價（USD/L）'].round(2)
    out = out.sort_values('進口總值（十億 USD）', ascending=False).reset_index(drop=True)
    out.insert(0, '排名', np.arange(1, len(out) + 1))
    save_table(out.set_index('排名'), 'ch4_market_segments')


# ============================================================
# main
# ============================================================
def run():
    print('🎯 Ch.4 — Premiumization 策略整合')
    fig4_1_dashboard()
    fig4_2_import_market_matrix()
    print('  ✅ Ch.4 done')


if __name__ == '__main__':
    run()
