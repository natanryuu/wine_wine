"""
🍷 葡萄酒市場競爭分析 — 期末報告圖表產生器
===========================================
資料來源：
  (a) UN Comtrade, HS 2204 → data/un_comtrade_wine_clean.csv
  (b) Wine Enthusiast via Kaggle → data/rose_wines_dataset.csv

產出：
  output/a1_export_market_share.png
  output/a2_export_unit_price.png
  output/a3_export_category_structure_2024.png
  output/a4_import_market_2024.png
  output/b1_rose_competitive_position.png
  output/b2_rose_price_tier.png
  output/b3_france_provinces.png
  output/b4_rose_rating_distribution.png
  output/analysis_summary.csv
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import seaborn as sns

# ============================================================
# 字體：繁體中文
# ============================================================
matplotlib.rcParams['font.sans-serif'] = [
    'Taipei Sans TC Beta', 'Microsoft JhengHei', 'Noto Sans CJK TC',
    'PingFang TC', 'Heiti TC', 'Arial Unicode MS', 'sans-serif'
]
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 路徑
# ============================================================
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

UN_CSV = os.path.join(DATA_DIR, "un_comtrade_wine_clean.csv")
ROSE_CSV = os.path.join(DATA_DIR, "rose_wines_dataset.csv")

# ============================================================
# 配色（馬卡龍系）
# ============================================================
COLORS = {
    'France': '#6B7FD7', 'Italy': '#7EC4A5', 'Spain': '#F4A261',
    'USA': '#E07A97', 'Chile': '#D4A574', 'Australia': '#82B1D4',
    'South Africa': '#A8D5A2', 'Argentina': '#B8B0C8',
    'Portugal': '#E8C170', 'Germany': '#9BCFC0',
    'Austria': '#C8B4D6',
    'Provence': '#8B6DB0',
    'bg': '#FAFAF7', 'grid': '#E8E6E0',
    'text': '#3D3D3D', 'text2': '#8A8A8A',
}

# 國名 中→英 / 英→中 對照
EN_TO_ZH = {
    'France': '法國', 'Italy': '義大利', 'Spain': '西班牙',
    'USA': '美國', 'United States': '美國', 'US': '美國',
    'Chile': '智利', 'Australia': '澳洲',
    'South Africa': '南非', 'Argentina': '阿根廷',
    'Portugal': '葡萄牙', 'Germany': '德國',
    'United Kingdom': '英國', 'UK': '英國',
    'Canada': '加拿大', 'Japan': '日本',
    'China': '中國', 'Netherlands': '荷蘭',
    'Hong Kong': '香港', 'Macao': '澳門',
    'New Zealand': '紐西蘭',
    'Austria': '奧地利',
    'Provence': '普羅旺斯',
    'France_Other': '法國其他產區',
}

EXPORTER_COUNTRIES = [
    'France', 'Italy', 'Spain', 'Chile',
    'Australia', 'South Africa', 'Argentina', 'USA',
]

# ============================================================
# 通用樣式
# ============================================================
def style_axes(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(COLORS['bg'])
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold',
                     color=COLORS['text'], pad=15)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12, color=COLORS['text'])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12, color=COLORS['text'])
    ax.tick_params(colors=COLORS['text'], labelsize=10)
    ax.grid(True, color=COLORS['grid'], linestyle='--', alpha=0.7, linewidth=0.8)
    ax.set_axisbelow(True)
    sns.despine(ax=ax)


def add_source_note(fig, source_text):
    fig.text(0.99, 0.01, source_text, ha='right', va='bottom',
             fontsize=8, color=COLORS['text2'], style='italic')


def save_fig(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.patch.set_facecolor(COLORS['bg'])
    fig.savefig(path, dpi=300, bbox_inches='tight',
                facecolor=COLORS['bg'])
    plt.close(fig)
    print(f"  💾 {filename}")
    return path


def get_color(country):
    return COLORS.get(country, '#999999')


# ============================================================
# 載入資料
# ============================================================
def load_data():
    if not os.path.exists(UN_CSV):
        raise FileNotFoundError(
            f"找不到 {UN_CSV}\n"
            f"請先準備清理過的 UN Comtrade 資料（含 commodity_short / volume_litres / "
            f"price_per_litre / price_per_bottle_750ml 衍生欄位）"
        )
    if not os.path.exists(ROSE_CSV):
        raise FileNotFoundError(f"找不到 {ROSE_CSV}")

    un = pd.read_csv(UN_CSV)
    rose = pd.read_csv(ROSE_CSV)

    # 標準化國名：美國統一為 USA；香港/澳門保留但簡化標籤
    un['country'] = un['country'].replace({
        'United States': 'USA', 'US': 'USA',
        'China, Hong Kong SAR': 'Hong Kong',
        'China, Macao SAR': 'Macao',
    })
    rose['country'] = rose['country'].replace({'US': 'USA', 'United States': 'USA'})

    return un, rose


# ============================================================
# 圖 a-1：主要出口國市占率趨勢
# ============================================================
def chart_a1(un, summary):
    df = un[(un['flow'] == 'Export') & (un['commodity_short'] == 'Still_Bottled')].copy()
    df = df[df['country'].isin(EXPORTER_COUNTRIES)]

    yearly = df.groupby(['year', 'country'])['trade_usd'].sum().reset_index()
    total_per_year = df.groupby('year')['trade_usd'].sum().rename('total')
    yearly = yearly.merge(total_per_year, on='year')
    yearly['share_pct'] = yearly['trade_usd'] / yearly['total'] * 100

    fig, ax = plt.subplots(figsize=(12, 7))
    style_axes(ax,
               title='主要出口國瓶裝靜態葡萄酒出口值市占率（2019-2024）',
               xlabel='年份', ylabel='市占率（%）')

    last_year = yearly['year'].max()
    countries_sorted = (yearly[yearly['year'] == last_year]
                        .sort_values('share_pct', ascending=False)['country'].tolist())

    for c in countries_sorted:
        sub = yearly[yearly['country'] == c].sort_values('year')
        ax.plot(sub['year'], sub['share_pct'],
                marker='o', linewidth=2.2, markersize=6,
                color=get_color(c), label=EN_TO_ZH.get(c, c))
        # 標註最新年份
        last = sub[sub['year'] == last_year]
        if not last.empty:
            v = last['share_pct'].values[0]
            ax.annotate(f'{v:.1f}%',
                        xy=(last_year, v),
                        xytext=(6, 0), textcoords='offset points',
                        fontsize=9, color=get_color(c), va='center',
                        fontweight='bold')

    ax.legend(loc='center left', bbox_to_anchor=(1.06, 0.5),
              frameon=False, fontsize=10)
    ax.set_xticks(sorted(yearly['year'].unique()))

    add_source_note(fig, '資料來源：UN Comtrade, HS 2204')
    save_fig(fig, 'a1_export_market_share.png')

    summary['a1_market_share'] = (
        yearly.pivot(index='year', columns='country', values='share_pct').round(2)
    )


# ============================================================
# 圖 a-2：出口單價趨勢
# ============================================================
def chart_a2(un, summary):
    df = un[(un['flow'] == 'Export') & (un['commodity_short'] == 'Still_Bottled')].copy()
    df = df[df['country'].isin(EXPORTER_COUNTRIES)]

    # 每國每年的單價：用 trade_usd / volume_litres × 0.75 較穩
    agg = df.groupby(['year', 'country']).agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum')
    ).reset_index()
    agg['price_per_bottle'] = (agg['trade'] / agg['vol']) * 0.75

    # 全球加權平均（用所有國家的 trade & vol）
    global_avg = df.groupby('year').apply(
        lambda g: (g['trade_usd'].sum() / g['volume_litres'].sum()) * 0.75
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    style_axes(ax,
               title='瓶裝靜態葡萄酒出口單價趨勢（美元/每瓶 750ml）',
               xlabel='年份', ylabel='單價（美元/750ml）')

    last_year = agg['year'].max()
    countries_sorted = (agg[agg['year'] == last_year]
                        .sort_values('price_per_bottle', ascending=False)['country'].tolist())

    for c in countries_sorted:
        sub = agg[agg['country'] == c].sort_values('year')
        ax.plot(sub['year'], sub['price_per_bottle'],
                marker='o', linewidth=2.2, markersize=6,
                color=get_color(c), label=EN_TO_ZH.get(c, c))
        last = sub[sub['year'] == last_year]
        if not last.empty:
            v = last['price_per_bottle'].values[0]
            ax.annotate(f'${v:.2f}',
                        xy=(last_year, v),
                        xytext=(6, 0), textcoords='offset points',
                        fontsize=9, color=get_color(c), va='center',
                        fontweight='bold')

    # 全球平均虛線
    ax.plot(global_avg.index, global_avg.values,
            color=COLORS['text2'], linestyle='--', linewidth=1.5,
            label='全球平均價', alpha=0.8)

    ax.legend(loc='center left', bbox_to_anchor=(1.06, 0.5),
              frameon=False, fontsize=10)
    ax.set_xticks(sorted(agg['year'].unique()))

    add_source_note(fig, '資料來源：UN Comtrade, HS 2204')
    save_fig(fig, 'a2_export_unit_price.png')

    summary['a2_unit_price'] = (
        agg.pivot(index='year', columns='country', values='price_per_bottle').round(2)
    )


# ============================================================
# 圖 a-3：2024 出口品類結構（按量 + 按值 兩張）
# ============================================================
A3_CATS = ['Still_Bottled', 'Still_Bulk', 'Sparkling', 'Still_2to10L']
A3_CAT_ZH = {'Still_Bottled': '瓶裝量', 'Still_Bulk': '散裝量',
             'Sparkling': '氣泡量', 'Still_2to10L': '中容量'}
A3_CAT_ZH_VAL = {'Still_Bottled': '瓶裝值', 'Still_Bulk': '散裝值',
                 'Sparkling': '氣泡值', 'Still_2to10L': '中容量值'}
A3_CAT_COLOR = {'Still_Bottled': COLORS['France'],
                'Still_Bulk': COLORS['Chile'],
                'Sparkling': COLORS['Spain'],
                'Still_2to10L': COLORS['Italy']}


def _filter_volume_complete(df):
    """
    踢掉 volume 回報有「主類別大缺漏」的國家。
    判準：Still_Bottled 是主要瓶裝類別，trade_usd 通常最大。
    若該類別 trade_usd > 50M 但 volume_litres 缺失 → 結構圖會嚴重失真，整國排除。
    （次要類別 Still_Bulk / Still_2to10L 缺漏只會少一塊，不踢國家）
    """
    bad = set()
    for country in df['country'].unique():
        sub = df[(df['country'] == country) & (df['commodity_short'] == 'Still_Bottled')]
        if sub.empty:
            continue
        trade = sub['trade_usd'].sum()
        vol = sub['volume_litres'].sum()
        if trade > 50_000_000 and (pd.isna(vol) or vol == 0):
            bad.add(country)
    if bad:
        print(f"     ⚠️  a3 按量：排除 Still_Bottled 體積缺漏的國家：{sorted(bad)}")
    return df[~df['country'].isin(bad)].copy()


def _render_a3(df, metric, title, label_dict, filename, summary, summary_key):
    pivot = (df.groupby(['country', 'commodity_short'])[metric]
               .sum().unstack(fill_value=0))
    for c in A3_CATS:
        if c not in pivot.columns:
            pivot[c] = 0
    pivot = pivot[A3_CATS]

    pivot = pivot[pivot.sum(axis=1) > 0]
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    pivot_pct = pivot_pct.sort_values('Still_Bottled', ascending=True)

    fig, ax = plt.subplots(figsize=(12, max(5, 0.45 * len(pivot_pct))))
    style_axes(ax, title=title, xlabel='占比（%）', ylabel='')

    countries_zh = [EN_TO_ZH.get(c, c) for c in pivot_pct.index]
    left = np.zeros(len(pivot_pct))
    for cat in A3_CATS:
        vals = pivot_pct[cat].values
        ax.barh(countries_zh, vals, left=left,
                color=A3_CAT_COLOR[cat], label=label_dict[cat],
                edgecolor='white', linewidth=0.6)
        left += vals

    ax.set_xlim(0, 100)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.12),
              ncol=4, frameon=False, fontsize=10)

    add_source_note(fig, '資料來源：UN Comtrade, HS 2204')
    save_fig(fig, filename)
    summary[summary_key] = pivot_pct.round(2)


def chart_a3(un, summary):
    df = un[(un['flow'] == 'Export') & (un['year'] == 2024)].copy()

    # a3 按量：排除 volume 不完整的國家（如 UK、HK）
    df_vol = _filter_volume_complete(df)
    _render_a3(df_vol, 'volume_litres',
               '2024 年各國葡萄酒出口品類結構（按量）',
               A3_CAT_ZH,
               'a3_export_category_structure_2024.png',
               summary, 'a3_category_structure_volume')

    # a3b 按值：trade_usd 全國皆可呈現
    _render_a3(df, 'trade_usd',
               '2024 年各國葡萄酒出口品類結構（按值）',
               A3_CAT_ZH_VAL,
               'a3b_export_category_structure_2024_value.png',
               summary, 'a3_category_structure_value')


# ============================================================
# 圖 a-4：2024 進口市場（氣泡圖）
# ============================================================
def chart_a4(un, summary):
    df = un[(un['flow'] == 'Import') & (un['year'] == 2024)].copy()

    agg = df.groupby('country').agg(
        trade=('trade_usd', 'sum'),
        vol=('volume_litres', 'sum')
    ).reset_index()
    agg['unit_price'] = agg['trade'] / agg['vol']  # USD per litre
    agg = agg[agg['vol'] > 0]

    # 取進口值前 12 大
    agg = agg.sort_values('trade', ascending=False).head(12)

    fig, ax = plt.subplots(figsize=(12, 7))
    style_axes(ax,
               title='2024 年主要葡萄酒進口市場（規模 vs 單價）',
               xlabel='進口總值（億美元）', ylabel='進口單價（美元/公升）')

    x = agg['trade'].values / 1e9  # 億 USD
    y = agg['unit_price'].values
    s = (agg['vol'].values / agg['vol'].max()) * 1800 + 80

    for i, row in agg.reset_index(drop=True).iterrows():
        c = get_color(row['country'])
        ax.scatter(x[i], y[i], s=s[i], color=c,
                   alpha=0.55, edgecolor=c, linewidth=2)
        ax.annotate(EN_TO_ZH.get(row['country'], row['country']),
                    xy=(x[i], y[i]),
                    ha='center', va='center',
                    fontsize=10, fontweight='bold',
                    color=COLORS['text'])

    add_source_note(fig, '資料來源：UN Comtrade, HS 2204')
    save_fig(fig, 'a4_import_market_2024.png')

    summary['a4_import_market'] = agg.set_index('country').round(3)


# ============================================================
# 圖 b-1：粉紅酒競爭定位（氣泡圖）
# ============================================================
def chart_b1(rose, summary):
    df = rose[rose['price'].notna() & rose['points'].notna()].copy()

    # 法國分成 普羅旺斯 / 其他
    fr = df[df['country'] == 'France'].copy()
    prov = fr[fr['is_provence'] == 1].copy()
    fr_other = fr[fr['is_provence'] != 1].copy()

    others = df[df['country'] != 'France'].copy()

    rows = []

    def agg_block(sub, label):
        if len(sub) < 20:
            return None
        return {
            'label': label,
            'avg_price': sub['price'].mean(),
            'avg_rating': sub['points'].mean(),
            'count': len(sub),
        }

    if (r := agg_block(fr_other, 'France_Other')) is not None:
        rows.append(r)
    if (r := agg_block(prov, 'Provence')) is not None:
        rows.append(r)

    for c in ['USA', 'Italy', 'Spain', 'Portugal', 'Austria',
              'Germany', 'Argentina', 'Chile']:
        sub = others[others['country'] == c]
        r = agg_block(sub, c)
        if r is not None:
            rows.append(r)

    pos = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(12, 7))
    style_axes(ax,
               title='全球粉紅酒競爭定位圖（單價 vs 品質）',
               xlabel='平均價格（美元）', ylabel='平均評分（分）')

    sizes = (pos['count'] / pos['count'].max()) * 1800 + 80
    for i, row in pos.iterrows():
        is_provence = row['label'] == 'Provence'
        c = COLORS['Provence'] if is_provence else get_color(row['label'])
        edge_lw = 2.5 if is_provence else 2
        alpha = 0.75 if is_provence else 0.55
        ax.scatter(row['avg_price'], row['avg_rating'], s=sizes[i],
                   color=c, alpha=alpha, edgecolor=c, linewidth=edge_lw)
        ax.annotate(EN_TO_ZH.get(row['label'], row['label']),
                    xy=(row['avg_price'], row['avg_rating']),
                    ha='center', va='center',
                    fontsize=10,
                    fontweight='bold' if is_provence else 'normal',
                    color=COLORS['text'])

    # 氣泡大小說明
    ax.text(0.98, 0.02, '圓圈大小 = 酒款數量',
            transform=ax.transAxes,
            ha='right', va='bottom',
            fontsize=9, color=COLORS['text2'], style='italic')

    add_source_note(fig, '資料來源：Wine Enthusiast Magazine via Kaggle')
    save_fig(fig, 'b1_rose_competitive_position.png')

    summary['b1_competitive_position'] = pos.set_index('label').round(2)


# ============================================================
# 圖 b-2：價格帶分布（堆疊橫條）
# ============================================================
def chart_b2(rose, summary):
    targets = ['France', 'USA', 'Italy', 'Spain',
               'Portugal', 'Austria', 'Argentina', 'Chile']
    df = rose[rose['country'].isin(targets) & rose['price_tier'].notna()].copy()

    tier_order = ['under_10', '10_15', '15_20', '20_30',
                  '30_50', '50_100', '100_plus']
    tier_zh = {'under_10': '<$10', '10_15': '$10-15', '15_20': '$15-20',
               '20_30': '$20-30', '30_50': '$30-50',
               '50_100': '$50-100', '100_plus': '$100+'}

    ct = pd.crosstab(df['country'], df['price_tier'], normalize='index') * 100
    for t in tier_order:
        if t not in ct.columns:
            ct[t] = 0
    ct = ct[tier_order]

    # 按中位價排序（用 price 中位數）
    median_price = df.groupby('country')['price'].median()
    ct = ct.loc[median_price.sort_values(ascending=True).index]

    # 漸層色
    cmap = LinearSegmentedColormap.from_list(
        'tier', ['#F0E6D3', '#8B6DB0'], N=len(tier_order))
    tier_colors = [cmap(i / (len(tier_order) - 1)) for i in range(len(tier_order))]

    fig, ax = plt.subplots(figsize=(12, max(5, 0.55 * len(ct))))
    style_axes(ax,
               title='各國粉紅酒價格帶分布',
               xlabel='占比（%）', ylabel='')

    countries_zh = [EN_TO_ZH.get(c, c) for c in ct.index]
    left = np.zeros(len(ct))
    for i, t in enumerate(tier_order):
        vals = ct[t].values
        ax.barh(countries_zh, vals, left=left,
                color=tier_colors[i], label=tier_zh[t],
                edgecolor='white', linewidth=0.6)
        left += vals

    ax.set_xlim(0, 100)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.18),
              ncol=7, frameon=False, fontsize=9)

    add_source_note(fig, '資料來源：Wine Enthusiast Magazine via Kaggle')
    save_fig(fig, 'b2_rose_price_tier.png')

    summary['b2_price_tier'] = ct.round(2)


# ============================================================
# 圖 b-3：法國各產區
# ============================================================
def chart_b3(rose, summary):
    fr = rose[(rose['country'] == 'France') &
              rose['price'].notna() &
              rose['points'].notna() &
              rose['province'].notna()].copy()

    grp = fr.groupby('province').agg(
        avg_price=('price', 'mean'),
        avg_rating=('points', 'mean'),
        count=('price', 'count')
    ).reset_index()
    grp = grp[grp['count'] >= 5]
    grp = grp.sort_values('count', ascending=True)

    fig, ax = plt.subplots(figsize=(12, max(5, 0.45 * len(grp))))
    style_axes(ax,
               title='法國各產區粉紅酒比較（單價 & 評分）',
               xlabel='平均價格（美元）', ylabel='')

    colors = [COLORS['Provence'] if p == 'Provence' else '#C4B7D4'
              for p in grp['province']]

    bars = ax.barh(grp['province'], grp['avg_price'],
                   color=colors, edgecolor='white', linewidth=0.6)

    xmax = grp['avg_price'].max()
    for bar, (_, row) in zip(bars, grp.iterrows()):
        w = bar.get_width()
        ax.text(w + xmax * 0.015, bar.get_y() + bar.get_height() / 2,
                f"均分 {row['avg_rating']:.1f} | {int(row['count'])} 款",
                va='center', fontsize=9, color=COLORS['text'])

    ax.set_xlim(0, xmax * 1.30)

    add_source_note(fig, '資料來源：Wine Enthusiast Magazine via Kaggle')
    save_fig(fig, 'b3_france_provinces.png')

    summary['b3_france_provinces'] = grp.set_index('province').round(2)


# ============================================================
# 圖 b-4：評分分布（箱形圖）
# ============================================================
def chart_b4(rose, summary):
    targets = ['France', 'USA', 'Italy', 'Spain',
               'Portugal', 'Austria', 'Germany',
               'Argentina', 'Chile', 'South Africa', 'Australia']
    df = rose[rose['country'].isin(targets) & rose['points'].notna()].copy()

    medians = df.groupby('country')['points'].median().sort_values(ascending=True)
    order = medians.index.tolist()
    df['country'] = pd.Categorical(df['country'], categories=order, ordered=True)
    df = df.sort_values('country')

    fig, ax = plt.subplots(figsize=(12, max(5, 0.55 * len(order))))
    style_axes(ax,
               title='各國粉紅酒評分分布',
               xlabel='Wine Enthusiast 評分（分）', ylabel='')

    palette = [get_color(c) for c in order]
    countries_zh = [EN_TO_ZH.get(c, c) for c in order]

    sns.boxplot(data=df, x='points', y='country', ax=ax,
                palette=palette, orient='h',
                width=0.6, fliersize=3,
                linewidth=1.2,
                boxprops=dict(alpha=0.75))
    ax.set_yticklabels(countries_zh)
    ax.set_ylabel('')

    add_source_note(fig, '資料來源：Wine Enthusiast Magazine via Kaggle')
    save_fig(fig, 'b4_rose_rating_distribution.png')

    desc = df.groupby('country')['points'].describe()[['count', 'mean', '50%', 'std']]
    summary['b4_rating_distribution'] = desc.round(2)


# ============================================================
# 匯出 analysis_summary.csv
# ============================================================
def export_summary(summary):
    blocks = []
    for key, df in summary.items():
        block = df.copy()
        block.insert(0, '_section', key)
        blocks.append(block)
        blocks.append(pd.DataFrame())  # 空行隔開
    out = pd.concat(blocks, axis=0)
    path = os.path.join(OUTPUT_DIR, 'analysis_summary.csv')
    out.to_csv(path, encoding='utf-8-sig')
    print(f"  💾 analysis_summary.csv")


# ============================================================
# main
# ============================================================
def main():
    print("🍷 葡萄酒市場競爭分析 — 圖表產生中")
    print(f"📂 輸出資料夾: {OUTPUT_DIR}")
    un, rose = load_data()
    print(f"  載入 UN: {len(un):,} 筆 / Rose: {len(rose):,} 筆\n")

    summary = {}

    print("─── 分析 (a) UN Comtrade ───")
    chart_a1(un, summary)
    chart_a2(un, summary)
    chart_a3(un, summary)
    chart_a4(un, summary)

    print("\n─── 分析 (b) Rose Wines ───")
    chart_b1(rose, summary)
    chart_b2(rose, summary)
    chart_b3(rose, summary)
    chart_b4(rose, summary)

    print("\n─── 匯出彙總 ───")
    export_summary(summary)

    print("\n🎉 完成！全部圖檔在 output/ 資料夾")


if __name__ == '__main__':
    main()
