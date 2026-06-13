"""
第 1 章：全球葡萄酒貿易與 Premiumization 趨勢
=============================================
產出：
  figures/fig1_0_market_share.png         — 8 國市占率趨勢
  figures/fig1_1_global_positioning.png   — 2024 出口國定位氣泡圖
  figures/fig1_2_france_volume_value.png  — 法國量跌值穩雙面板
  figures/fig1_3_price_trend.png          — 5 國 6 年單價趨勢
  tables/ch1_welch_test.csv               — 法國 vs 其他國家均價檢定
  tables/ch1_cagr_ranking.csv             — 各國 volume/value/price CAGR 排名
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from stage1._common import (
    DATA_DIR, PALETTE, get_color, country_label,
    style_axes, add_source_note, save_fig, save_table,
    welch_t, cagr,
)

UN_CSV = os.path.join(DATA_DIR, 'un_comtrade_wine_clean.csv')
SRC_NOTE = '資料來源：UN Comtrade, HS 2204'

EXPORTER_8 = ['France', 'Italy', 'Spain', 'Chile',
              'Australia', 'South Africa', 'Argentina', 'USA']
PRICE_TREND_5 = ['France', 'Italy', 'Spain', 'Australia', 'Chile']


def load_un():
    df = pd.read_csv(UN_CSV)
    df['country'] = df['country'].replace({
        'United States': 'USA', 'US': 'USA',
        'China, Hong Kong SAR': 'Hong Kong',
        'China, Macao SAR': 'Macao',
    })
    return df


# ============================================================
# Fig 1.0 — 8 國市占率趨勢（用新配色重繪）
# ============================================================
def fig1_0_market_share(un):
    df = un[(un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled') &
            (un['country'].isin(EXPORTER_8))].copy()

    yearly = df.groupby(['year', 'country'])['trade_usd'].sum().reset_index()
    total = df.groupby('year')['trade_usd'].sum().rename('total')
    yearly = yearly.merge(total, on='year')
    yearly['share_pct'] = yearly['trade_usd'] / yearly['total'] * 100

    fig, ax = plt.subplots(figsize=(11, 6.5))
    style_axes(ax,
               title='全球瓶裝靜態葡萄酒主要出口國市占率（2019-2024）',
               xlabel='年份', ylabel='出口值市占率（%）')

    last = yearly['year'].max()
    order = (yearly[yearly['year'] == last]
             .sort_values('share_pct', ascending=False)['country'].tolist())

    for c in order:
        sub = yearly[yearly['country'] == c].sort_values('year')
        is_fr = c == 'France'
        ax.plot(sub['year'], sub['share_pct'],
                marker='o', markersize=6,
                linewidth=3 if is_fr else 1.8,
                color=get_color(c),
                alpha=1.0 if is_fr else 0.85,
                label=country_label(c))
        v = sub[sub['year'] == last]['share_pct'].values
        if len(v):
            ax.annotate(f'{v[0]:.1f}%',
                        xy=(last, v[0]),
                        xytext=(6, 0), textcoords='offset points',
                        fontsize=9, color=get_color(c),
                        fontweight='bold' if is_fr else 'normal',
                        va='center')

    ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5),
              frameon=False, fontsize=10)
    ax.set_xticks(sorted(yearly['year'].unique()))
    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig1_0_market_share')


# ============================================================
# Fig 1.1 — 2024 出口國定位氣泡圖
# ============================================================
def fig1_1_global_positioning(un):
    df = un[(un['flow'] == 'Export') &
            (un['year'] == 2024) &
            (un['commodity_short'] == 'Still_Bottled')].copy()

    agg = df.groupby('country').agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg = agg[(agg['vol'] > 0) & (agg['trade'] > 0)]
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75
    agg['vol_million_L'] = agg['vol'] / 1e6

    # 取出口值 top 10
    agg = agg.sort_values('trade', ascending=False).head(10)

    # 全球加權均價
    global_price = (df['trade_usd'].sum() / df['volume_litres'].sum()) * 0.75
    fr = agg[agg['country'] == 'France']
    fr_price = fr['price'].values[0] if len(fr) else np.nan
    premium_x = fr_price / global_price if global_price > 0 else np.nan

    fig, ax = plt.subplots(figsize=(11, 7))
    style_axes(ax,
               title='2024 年全球瓶裝靜態葡萄酒出口國定位',
               xlabel='出口量（百萬公升）',
               ylabel='出口均價（美元/750ml）')

    agg = agg.reset_index(drop=True)
    sizes = ((agg['trade'] / agg['trade'].max()) * 2200 + 100).values
    for i, row in agg.iterrows():
        c = get_color(row['country'])
        ax.scatter(row['vol_million_L'], row['price'], s=sizes[i],
                   color=c, alpha=0.6, edgecolor=c, linewidth=2)
        # 主要標的（FR/IT/ES）標完整 國名+單價
        if row['country'] in ['France', 'Italy', 'Spain']:
            ax.annotate(f"{country_label(row['country'])}\n${row['price']:.2f}",
                        xy=(row['vol_million_L'], row['price']),
                        ha='center', va='center',
                        fontsize=10, fontweight='bold',
                        color=PALETTE['text'])
        else:
            ax.annotate(country_label(row['country']),
                        xy=(row['vol_million_L'], row['price']),
                        ha='center', va='center',
                        fontsize=9, color=PALETTE['text'])

    # 全球均價虛線
    ax.axhline(global_price, color=PALETTE['text2'],
               linestyle='--', linewidth=1.2, alpha=0.7)
    ax.text(ax.get_xlim()[1] * 0.98, global_price,
            f' 全球加權均價 ${global_price:.2f}',
            color=PALETTE['text2'], fontsize=9, va='bottom', ha='right')

    # 法國溢價文字（放右上，避開左上聚集的高價氣泡）
    if not np.isnan(premium_x):
        ax.text(0.98, 0.97,
                f'法國溢價：{premium_x:.2f}× 全球均價',
                transform=ax.transAxes,
                fontsize=11, fontweight='bold',
                color=PALETTE['France'],
                ha='right', va='top',
                bbox=dict(boxstyle='round,pad=0.4',
                          facecolor='white', edgecolor=PALETTE['France'],
                          linewidth=1.2, alpha=0.9))

    # 氣泡大小說明（左下）
    ax.text(0.02, 0.02, '圓圈大小 = 出口值',
            transform=ax.transAxes, ha='left', va='bottom',
            fontsize=9, color=PALETTE['text2'], style='italic')

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig1_1_global_positioning')


# ============================================================
# Fig 1.2 — 法國「量跌值穩」雙面板
# ============================================================
def fig1_2_france_volume_value(un):
    df = un[(un['country'] == 'France') &
            (un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled')].copy()
    df = df.sort_values('year')

    agg = df.groupby('year').agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75
    agg['trade_b'] = agg['trade'] / 1e9
    agg['vol_m'] = agg['vol'] / 1e6

    years = agg['year'].values
    n_periods = len(years) - 1  # 5 期 (2019→2024)
    cagr_value = cagr(agg['trade_b'].iloc[0], agg['trade_b'].iloc[-1], n_periods)
    cagr_volume = cagr(agg['vol_m'].iloc[0], agg['vol_m'].iloc[-1], n_periods)
    cagr_price = cagr(agg['price'].iloc[0], agg['price'].iloc[-1], n_periods)

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(11, 8),
                                          sharex=True,
                                          gridspec_kw={'height_ratios': [1.3, 1]})

    # 上：出口值（柱）+ 單價（右軸折線）
    style_axes(ax_top,
               title=f'法國瓶裝靜態葡萄酒出口（{int(years[0])}–{int(years[-1])}）',
               ylabel='出口值（十億美元）')
    bars = ax_top.bar(years, agg['trade_b'],
                      color=PALETTE['France'], alpha=0.75,
                      edgecolor='white', linewidth=1.2,
                      label='出口值（十億 USD）')
    for b, v in zip(bars, agg['trade_b']):
        ax_top.text(b.get_x() + b.get_width() / 2, v + 0.05,
                    f'{v:.2f}', ha='center', va='bottom',
                    fontsize=9, color=PALETTE['France'],
                    fontweight='bold')

    ax_top2 = ax_top.twinx()
    ax_top2.plot(years, agg['price'],
                 marker='o', linewidth=2.5, markersize=7,
                 color=PALETTE['Rose'], label='每瓶均價（USD/750ml）')
    for x, p in zip(years, agg['price']):
        ax_top2.annotate(f'${p:.2f}',
                          xy=(x, p), xytext=(0, 10),
                          textcoords='offset points',
                          fontsize=8.5, color=PALETTE['Rose'],
                          fontweight='bold', ha='center')
    ax_top2.set_ylabel('每瓶均價（USD/750ml）', color=PALETTE['Rose'], fontsize=11)
    ax_top2.tick_params(axis='y', colors=PALETTE['Rose'], labelsize=9)
    ax_top2.spines['right'].set_color(PALETTE['Rose'])
    ax_top2.spines['top'].set_visible(False)
    ax_top2.grid(False)

    # legend (合併兩軸)
    lines1, labels1 = ax_top.get_legend_handles_labels()
    lines2, labels2 = ax_top2.get_legend_handles_labels()
    ax_top.legend(lines1 + lines2, labels1 + labels2,
                  loc='upper left', frameon=False, fontsize=9)

    # 下：出口量
    style_axes(ax_bot,
               xlabel='年份', ylabel='出口量（百萬公升）')
    ax_bot.plot(years, agg['vol_m'],
                marker='s', linewidth=2.5, markersize=7,
                color=PALETTE['Global'], label='出口量')
    ax_bot.fill_between(years, agg['vol_m'], alpha=0.18,
                        color=PALETTE['Global'])
    for x, v in zip(years, agg['vol_m']):
        ax_bot.annotate(f'{v:.0f}',
                        xy=(x, v), xytext=(0, 9),
                        textcoords='offset points',
                        fontsize=9, color=PALETTE['Global'],
                        fontweight='bold', ha='center')
    ax_bot.set_xticks(years)

    # CAGR 標註（放在出口量面板右側中段，避開折線）
    cagr_str = (f'CAGR {int(years[0])}→{int(years[-1])}\n'
                f'  出口值 {cagr_value*100:+.1f}%\n'
                f'  出口量 {cagr_volume*100:+.1f}%\n'
                f'  每瓶均價 {cagr_price*100:+.1f}%')
    ax_bot.text(0.99, 0.40, cagr_str,
                transform=ax_bot.transAxes,
                ha='right', va='center', fontsize=9,
                color=PALETTE['text'],
                bbox=dict(boxstyle='round,pad=0.4',
                          facecolor='white', edgecolor=PALETTE['text2'],
                          linewidth=0.8, alpha=0.9))

    add_source_note(fig, SRC_NOTE)
    plt.tight_layout()
    save_fig(fig, 'fig1_2_france_volume_value')


# ============================================================
# Fig 1.3 — 5 國 6 年單價趨勢
# ============================================================
def fig1_3_price_trend(un):
    df = un[(un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled') &
            (un['country'].isin(PRICE_TREND_5))].copy()

    agg = df.groupby(['year', 'country']).agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg = agg[agg['vol'] > 0]
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75
    agg = agg[np.isfinite(agg['price'])]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    style_axes(ax,
               title='主要出口國瓶裝靜態葡萄酒單價趨勢（2019-2024）',
               xlabel='年份', ylabel='每瓶均價（USD/750ml）')

    last = agg['year'].max()
    order = (agg[agg['year'] == last]
             .sort_values('price', ascending=False)['country'].tolist())

    for c in order:
        sub = agg[agg['country'] == c].sort_values('year')
        is_fr = c == 'France'
        ax.plot(sub['year'], sub['price'],
                marker='o', markersize=7,
                linewidth=3 if is_fr else 1.8,
                color=get_color(c),
                alpha=1.0 if is_fr else 0.85,
                label=country_label(c))
        v = sub[sub['year'] == last]['price'].values
        if len(v):
            ax.annotate(f'${v[0]:.2f}',
                        xy=(last, v[0]),
                        xytext=(6, 0), textcoords='offset points',
                        fontsize=9, color=get_color(c),
                        fontweight='bold' if is_fr else 'normal',
                        va='center')

    ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.5),
              frameon=False, fontsize=10)
    ax.set_xticks(sorted(agg['year'].unique()))

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig1_3_price_trend')


# ============================================================
# Table 1.1 — Welch's t-test：法國 vs 其他國家年度均價
# ============================================================
def table1_1_welch_test(un):
    df = un[(un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled')].copy()

    agg = df.groupby(['year', 'country']).agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg = agg[(agg['vol'] > 0) & agg['vol'].notna()]
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75
    agg = agg[agg['price'].notna() & np.isfinite(agg['price']) & (agg['price'] > 0)]

    fr_prices = agg[agg['country'] == 'France']['price']
    others = agg[(agg['country'] != 'France') &
                 agg['country'].isin(EXPORTER_8)]['price']

    res_overall = welch_t(fr_prices, others)

    rows = [{
        '比較組': '法國 vs 其他 7 國（合併）',
        'n_法國': res_overall['n_a'],
        'n_對照組': res_overall['n_b'],
        '法國均價(USD/750ml)': round(res_overall['mean_a'], 3),
        '對照均價(USD/750ml)': round(res_overall['mean_b'], 3),
        't 值': round(res_overall['t'], 3),
        'p 值': res_overall['p'],
        '顯著': res_overall['sig'],
    }]

    # 逐國比較
    for c in PRICE_TREND_5:
        if c == 'France':
            continue
        sub = agg[agg['country'] == c]['price']
        if len(sub) < 2:
            continue
        r = welch_t(fr_prices, sub)
        rows.append({
            '比較組': f'法國 vs {country_label(c)}',
            'n_法國': r['n_a'],
            'n_對照組': r['n_b'],
            '法國均價(USD/750ml)': round(r['mean_a'], 3),
            '對照均價(USD/750ml)': round(r['mean_b'], 3),
            't 值': round(r['t'], 3),
            'p 值': r['p'],
            '顯著': r['sig'],
        })

    out = pd.DataFrame(rows)
    out['p 值'] = out['p 值'].apply(lambda v: f'{v:.2e}')
    save_table(out, 'ch1_welch_test')


# ============================================================
# Table 1.2 — 各國 CAGR 排名
# ============================================================
def table1_2_cagr_ranking(un):
    df = un[(un['flow'] == 'Export') &
            (un['commodity_short'] == 'Still_Bottled') &
            (un['country'].isin(EXPORTER_8))].copy()

    agg = df.groupby(['year', 'country']).agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum'),
    ).reset_index()
    agg['price'] = (agg['trade'] / agg['vol']) * 0.75

    rows = []
    for c in EXPORTER_8:
        sub = agg[agg['country'] == c].sort_values('year')
        if len(sub) < 2:
            continue
        first, last = sub.iloc[0], sub.iloc[-1]
        n_periods = len(sub) - 1

        rows.append({
            '國家': country_label(c),
            'volume CAGR (%)': round(cagr(first['vol'], last['vol'], n_periods) * 100, 2),
            'value CAGR (%)':  round(cagr(first['trade'], last['trade'], n_periods) * 100, 2),
            'price CAGR (%)':  round(cagr(first['price'], last['price'], n_periods) * 100, 2),
            'volume 2019 (M L)': round(first['vol'] / 1e6, 1),
            'volume 2024 (M L)': round(last['vol'] / 1e6, 1),
            'price 2024 ($/瓶)': round(last['price'], 2),
        })

    out = pd.DataFrame(rows).sort_values('value CAGR (%)', ascending=False)
    save_table(out, 'ch1_cagr_ranking')


# ============================================================
# main
# ============================================================
def run():
    print('🌍 Ch.1 — 全球葡萄酒貿易與 Premiumization')
    un = load_un()
    fig1_0_market_share(un)
    fig1_1_global_positioning(un)
    fig1_2_france_volume_value(un)
    fig1_3_price_trend(un)
    table1_1_welch_test(un)
    table1_2_cagr_ranking(un)
    print('  ✅ Ch.1 done')


if __name__ == '__main__':
    run()
