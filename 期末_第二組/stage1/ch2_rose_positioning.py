"""
第 2 章：Rosé 市場結構與 Provence 品質定位
==========================================
產出：
  figures/fig2_1_price_tier.png         — 4 國價格帶 100% 堆疊
  figures/fig2_2_france_regions.png     — 法國 11 產區氣泡圖
  figures/fig2_3_provence_vs_others.png — Provence vs 非 Provence 箱形圖
  figures/fig2_4_provence_terms.png     — TF-IDF Top 15 Provence 特徵詞
  tables/ch2_chi2.csv                   — 法國 vs 非法國 價格帶卡方檢定
  tables/ch2_provence_test.csv          — Provence vs 非 Provence 檢定
  tables/ch2_provence_terms.csv         — TF-IDF 特徵詞權重表
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from stage1._common import (
    DATA_DIR, PALETTE, get_color, country_label,
    style_axes, add_source_note, save_fig, save_table,
    chi2_test, mann_whitney, cohen_d, rank_biserial,
)

ROSE_CSV = os.path.join(DATA_DIR, 'rose_wines_dataset.csv')
PRICE_TIER_CSV = os.path.join(DATA_DIR, 'rose_price_tier_by_country.csv')
FR_REGION_CSV = os.path.join(DATA_DIR, 'france_rose_by_region.csv')

SRC_NOTE = '資料來源：Wine Enthusiast Magazine via Kaggle'

TIER_ORDER = ['under_10', '10_15', '15_20', '20_30', '30_50', '50_100', '100_plus']
TIER_ZH = {
    'under_10': '<$10', '10_15': '$10-15', '15_20': '$15-20',
    '20_30': '$20-30', '30_50': '$30-50',
    '50_100': '$50-100', '100_plus': '$100+',
}

PROVINCE_ZH = {
    'Provence': '普羅旺斯',
    'Champagne': '香檳區',
    'Bordeaux': '波爾多',
    'Loire Valley': '羅亞爾河',
    'Rhône Valley': '隆河',
    'Languedoc-Roussillon': '朗格多克',
    'France Other': '法國其他',
    'Alsace': '阿爾薩斯',
    'Southwest France': '西南法國',
    'Beaujolais': '薄酒萊',
    'Burgundy': '勃根第',
}


# ============================================================
# Fig 2.1 — 4 國價格帶 100% 堆疊長條
# ============================================================
def fig2_1_price_tier():
    df = pd.read_csv(PRICE_TIER_CSV)
    targets = ['France', 'US', 'Italy', 'Spain']

    # 取 4 國 + 7 個 tier，計算百分比
    sub = df[df['price_tier'].isin(TIER_ORDER)].set_index('price_tier')[targets]
    sub = sub.reindex(TIER_ORDER)
    pct = (sub / sub.sum(axis=0)) * 100  # 每國各 tier 占比

    # 漸層色：低價淺 → 高價深紫紅
    cmap = LinearSegmentedColormap.from_list(
        'tier', ['#F0E6D3', PALETTE['Rose']], N=len(TIER_ORDER))
    tier_colors = [cmap(i / (len(TIER_ORDER) - 1)) for i in range(len(TIER_ORDER))]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    style_axes(ax, title=None, xlabel='占比（%）', ylabel='')

    # x = 各 tier 占比，y = 國家（橫條，每國一行）
    countries_zh = [country_label(c if c != 'US' else 'USA') for c in targets]
    pct_T = pct.T  # rows=country, cols=tier
    left = np.zeros(len(targets))
    for i, t in enumerate(TIER_ORDER):
        vals = pct_T[t].values
        bars = ax.barh(countries_zh, vals, left=left,
                       color=tier_colors[i], label=TIER_ZH[t],
                       edgecolor='white', linewidth=0.6)
        # 在每段中央標 % (>=5% 才標)
        for j, v in enumerate(vals):
            if v >= 5:
                ax.text(left[j] + v / 2, j, f'{v:.0f}%',
                        ha='center', va='center', fontsize=8.5,
                        color='white' if i >= 4 else PALETTE['text'],
                        fontweight='bold')
        left += vals

    ax.set_xlim(0, 100)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.18),
              ncol=7, frameon=False, fontsize=9)

    # 主標 + 副標（副標含關鍵 stat）—— 用 fig.suptitle 兩行避開覆蓋
    fr_30plus = pct['France'].loc[['30_50', '50_100', '100_plus']].sum()
    others_30plus = pct[['US', 'Italy', 'Spain']].loc[['30_50', '50_100', '100_plus']].sum().mean()
    fig.suptitle('全球 Rosé 價格帶分佈（4 大產區國）',
                 fontsize=15, fontweight='bold', color=PALETTE['text'],
                 y=0.99)
    fig.text(0.5, 0.93,
             f'法國 $30+ 高端帶占 {fr_30plus:.1f}%   |   其他國家平均 {others_30plus:.1f}%',
             ha='center', va='top',
             fontsize=11, color=PALETTE['France'], fontweight='bold')

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig2_1_price_tier')


# ============================================================
# Fig 2.2 — 法國 11 產區氣泡圖
# ============================================================
def fig2_2_france_regions():
    df = pd.read_csv(FR_REGION_CSV)

    fig, ax = plt.subplots(figsize=(11, 7))
    style_axes(ax,
               title='法國 11 個 Rosé 產區定位（價格 vs 評分 vs 數量）',
               xlabel='平均價格（美元）', ylabel='平均評分（分）')

    sizes = (df['wine_count'] / df['wine_count'].max()) * 2200 + 150
    for i, row in df.iterrows():
        is_prov = row['province'] == 'Provence'
        c = PALETTE['Rose'] if is_prov else PALETTE['Global']
        alpha = 0.8 if is_prov else 0.45
        edge = 2.5 if is_prov else 1.5
        ax.scatter(row['avg_price'], row['avg_rating'],
                   s=sizes[i], color=c, alpha=alpha,
                   edgecolor=c, linewidth=edge)
        label = PROVINCE_ZH.get(row['province'], row['province'])
        # 香檳離得遠，用箭頭標
        ax.annotate(label,
                    xy=(row['avg_price'], row['avg_rating']),
                    ha='center', va='center',
                    fontsize=10 if is_prov else 9,
                    fontweight='bold' if is_prov else 'normal',
                    color=PALETTE['text'])

    # 普羅旺斯標榜
    prov = df[df['province'] == 'Provence'].iloc[0]
    note = (f"普羅旺斯：{int(prov['wine_count'])} 支、"
            f"${prov['avg_price']:.0f}、{prov['avg_rating']:.1f} 分\n"
            f"→ 數量第一、評分中高、價格中位 = 性價比王者")
    ax.text(0.02, 0.02, note,
            transform=ax.transAxes,
            fontsize=10, color=PALETTE['Rose'],
            fontweight='bold',
            ha='left', va='bottom',
            bbox=dict(boxstyle='round,pad=0.4',
                      facecolor='white', edgecolor=PALETTE['Rose'],
                      linewidth=1.2, alpha=0.9))

    ax.text(0.99, 0.02, '圓圈大小 = 酒款數量',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=9, color=PALETTE['text2'], style='italic')

    add_source_note(fig, SRC_NOTE)
    save_fig(fig, 'fig2_2_france_regions')


# ============================================================
# Fig 2.3 — Provence vs 非 Provence 箱形圖（價格 + 評分）
# ============================================================
def fig2_3_provence_vs_others():
    df = pd.read_csv(ROSE_CSV)
    df = df[df['price'].notna() & df['points'].notna()].copy()
    df['group'] = np.where(df['is_provence'] == 1, 'Provence', 'Non-Provence')

    fig, (ax_p, ax_r) = plt.subplots(1, 2, figsize=(12, 6))

    # 左：價格箱形
    style_axes(ax_p, title='價格分佈', xlabel='', ylabel='價格（美元）')
    data_p = [df[df['group'] == 'Provence']['price'].values,
              df[df['group'] == 'Non-Provence']['price'].values]
    bp_p = ax_p.boxplot(data_p, labels=['普羅旺斯', '非普羅旺斯'],
                         patch_artist=True, widths=0.5,
                         showfliers=True, flierprops=dict(marker='o', markersize=2,
                                                          markerfacecolor='gray',
                                                          markeredgecolor='none', alpha=0.4))
    box_colors = [PALETTE['Rose'], PALETTE['text2']]
    for patch, c in zip(bp_p['boxes'], box_colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
        patch.set_edgecolor(c)
    for med in bp_p['medians']:
        med.set_color('white')
        med.set_linewidth(2)

    # 截斷極端值方便看主分布
    p99 = np.percentile(df['price'], 99)
    ax_p.set_ylim(0, p99 * 1.05)
    # 中位數標註
    medians_p = [np.median(d) for d in data_p]
    for i, m in enumerate(medians_p):
        ax_p.text(i + 1, m, f' {m:.0f}', va='center', ha='left',
                  fontsize=10, color=box_colors[i], fontweight='bold')

    # 右：評分箱形
    style_axes(ax_r, title='評分分佈', xlabel='', ylabel='評分（分）')
    data_r = [df[df['group'] == 'Provence']['points'].values,
              df[df['group'] == 'Non-Provence']['points'].values]
    bp_r = ax_r.boxplot(data_r, labels=['普羅旺斯', '非普羅旺斯'],
                         patch_artist=True, widths=0.5,
                         showfliers=True, flierprops=dict(marker='o', markersize=2,
                                                          markerfacecolor='gray',
                                                          markeredgecolor='none', alpha=0.4))
    for patch, c in zip(bp_r['boxes'], box_colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
        patch.set_edgecolor(c)
    for med in bp_r['medians']:
        med.set_color('white')
        med.set_linewidth(2)

    medians_r = [np.median(d) for d in data_r]
    for i, m in enumerate(medians_r):
        ax_r.text(i + 1, m, f' {m:.1f}', va='center', ha='left',
                  fontsize=10, color=box_colors[i], fontweight='bold')

    fig.suptitle(f'Provence Rosé vs 非 Provence Rosé（n={len(df[df["is_provence"]==1])} vs {len(df[df["is_provence"]==0])}）',
                 fontsize=14, fontweight='bold', color=PALETTE['text'], y=1.02)

    add_source_note(fig, SRC_NOTE)
    plt.tight_layout()
    save_fig(fig, 'fig2_3_provence_vs_others')


# ============================================================
# Fig 2.4 + Table 2.3 — TF-IDF Top 15 Provence 特徵詞
# ============================================================
def fig2_4_provence_terms():
    from sklearn.feature_extraction.text import TfidfVectorizer

    df = pd.read_csv(ROSE_CSV)
    df = df[df['description'].notna()].copy()

    # 簡單清理
    def clean(text):
        text = str(text).lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        return text

    df['desc_clean'] = df['description'].apply(clean)

    prov_docs = df[df['is_provence'] == 1]['desc_clean'].tolist()
    other_docs = df[df['is_provence'] == 0]['desc_clean'].tolist()

    # 把所有文檔餵進去算 TF-IDF
    all_docs = prov_docs + other_docs
    labels = np.array([1] * len(prov_docs) + [0] * len(other_docs))

    # 在英文 stopwords 之上再加葡萄酒領域常見詞，避免 top 詞被通用詞占滿
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    domain_stop = {
        'wine', 'wines', 'rose', 'rosé', 'rosés', 'roses',
        'flavors', 'flavor', 'aromas', 'aroma', 'palate',
        'nose', 'notes', 'note', 'finish', 'mouth',
        'red', 'white', 'pink',
        'drink', 'drinks', 'drinking', 'bottle', 'glass',
        'taste', 'tastes', 'tasting',
        # 地名 / 產區名 — 排除避免 trivial leakage
        'provence', 'provencal', 'cotes', 'aix', 'bandol',
        'french', 'france',
    }
    stop_words = list(ENGLISH_STOP_WORDS.union(domain_stop))

    vec = TfidfVectorizer(
        stop_words=stop_words,
        max_features=2000,
        min_df=10,
        ngram_range=(1, 1),
    )
    X = vec.fit_transform(all_docs)
    terms = np.array(vec.get_feature_names_out())

    # 各組平均 TF-IDF
    prov_mean = np.asarray(X[labels == 1].mean(axis=0)).ravel()
    other_mean = np.asarray(X[labels == 0].mean(axis=0)).ravel()
    diff = prov_mean - other_mean

    # 取差異最大的（Provence > Non-Provence）top 15
    top_idx = np.argsort(diff)[::-1][:15]
    top_df = pd.DataFrame({
        'term': terms[top_idx],
        'provence_tfidf': prov_mean[top_idx],
        'non_provence_tfidf': other_mean[top_idx],
        'diff': diff[top_idx],
    }).sort_values('diff', ascending=True)  # 由小到大畫，最大在頂

    # 圖
    fig, ax = plt.subplots(figsize=(10, 7))
    style_axes(ax,
               title='Provence Rosé 的特徵詞（TF-IDF Top 15）',
               xlabel='TF-IDF 差異值（Provence − 非 Provence）',
               ylabel='')
    bars = ax.barh(top_df['term'], top_df['diff'],
                   color=PALETTE['Rose'], alpha=0.85,
                   edgecolor='white', linewidth=0.6)
    for bar, v in zip(bars, top_df['diff']):
        ax.text(v + top_df['diff'].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{v:.4f}',
                va='center', ha='left',
                fontsize=8.5, color=PALETTE['text'])

    ax.set_xlim(0, top_df['diff'].max() * 1.15)
    add_source_note(fig, SRC_NOTE + '；TF-IDF: scikit-learn')
    save_fig(fig, 'fig2_4_provence_terms')

    # 表（顯示完整 top 15，按 diff 由大到小）
    out = top_df.sort_values('diff', ascending=False).reset_index(drop=True)
    out['rank'] = np.arange(1, len(out) + 1)
    out = out[['rank', 'term', 'provence_tfidf', 'non_provence_tfidf', 'diff']]
    out['provence_tfidf'] = out['provence_tfidf'].round(5)
    out['non_provence_tfidf'] = out['non_provence_tfidf'].round(5)
    out['diff'] = out['diff'].round(5)
    save_table(out, 'ch2_provence_terms')


# ============================================================
# Table 2.1 — 卡方檢定（法國 vs 非法國 價格帶分佈）
# ============================================================
def table2_1_chi2():
    df = pd.read_csv(PRICE_TIER_CSV)
    sub = df[df['price_tier'].isin(TIER_ORDER)].set_index('price_tier')
    sub = sub.reindex(TIER_ORDER)

    # 法國 vs 非法國（除了 'All' 列）
    france = sub['France'].values
    cols_other = [c for c in sub.columns if c not in ['France', 'All']]
    non_france = sub[cols_other].sum(axis=1).values

    contingency = pd.DataFrame({
        '法國': france,
        '非法國': non_france,
    }, index=[TIER_ZH[t] for t in TIER_ORDER])

    res = chi2_test(contingency)

    out = pd.DataFrame([{
        '檢定': '法國 vs 非法國 價格帶分佈',
        'Chi² 值': round(res['chi2'], 2),
        '自由度': res['dof'],
        'p 值': f"{res['p']:.2e}",
        "Cramer's V": round(res['cramers_v'], 3),
        '顯著': res['sig'],
    }])
    save_table(out.set_index('檢定'), 'ch2_chi2')

    # 同時保存 contingency 表方便看分布
    contingency_pct = (contingency.div(contingency.sum(axis=0), axis=1) * 100).round(1)
    contingency_pct.columns = [c + ' %' for c in contingency_pct.columns]
    final = pd.concat([contingency, contingency_pct], axis=1)
    save_table(final, 'ch2_chi2_contingency')


# ============================================================
# Table 2.2 — Provence vs 非 Provence Mann-Whitney + Cohen's d + r
# ============================================================
def table2_2_provence_test():
    df = pd.read_csv(ROSE_CSV)

    rows = []
    for col, name in [('price', '價格'), ('points', '評分')]:
        sub = df[[col, 'is_provence']].dropna()
        prov = sub[sub['is_provence'] == 1][col].values
        other = sub[sub['is_provence'] == 0][col].values

        mw = mann_whitney(prov, other)
        d = cohen_d(prov, other)
        r = rank_biserial(prov, other)

        rows.append({
            '指標': name,
            'n_Provence': mw['n_a'],
            'n_非Provence': mw['n_b'],
            'Provence 中位': round(mw['median_a'], 2),
            '非 Provence 中位': round(mw['median_b'], 2),
            'Mann-Whitney U': int(mw['U']),
            'p 值': f"{mw['p']:.2e}",
            "Cohen's d": round(d, 3),
            'rank-biserial r': round(r, 3),
            '顯著': mw['sig'],
        })

    out = pd.DataFrame(rows).set_index('指標')
    save_table(out, 'ch2_provence_test')


# ============================================================
# main
# ============================================================
def run():
    print('🌹 Ch.2 — Rosé 市場結構與 Provence 品質定位')
    fig2_1_price_tier()
    fig2_2_france_regions()
    fig2_3_provence_vs_others()
    fig2_4_provence_terms()
    table2_1_chi2()
    table2_2_provence_test()
    print('  ✅ Ch.2 done')


if __name__ == '__main__':
    run()
