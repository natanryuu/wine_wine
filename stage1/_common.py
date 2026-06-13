"""
Stage 1 共用模組：字體、配色、圖表 / 表格輸出、統計工具
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# ============================================================
# 中文字體
# ============================================================
matplotlib.rcParams['font.sans-serif'] = [
    'Taipei Sans TC Beta', 'Microsoft JhengHei', 'Noto Sans CJK TC',
    'PingFang TC', 'Heiti TC', 'Arial Unicode MS', 'sans-serif'
]
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 路徑
# ============================================================
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT, 'data')
FIG_DIR = os.path.join(ROOT, 'figures')
TBL_DIR = os.path.join(ROOT, 'tables')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TBL_DIR, exist_ok=True)

# ============================================================
# 配色
# ============================================================
PALETTE = {
    'France':    '#1B7A5A',
    'Var':       '#1B7A5A',
    'BdR':       '#5B4EB5',
    'Bordeaux':  '#C43E3E',
    'Languedoc': '#B07316',
    'Vaucluse':  '#73726C',
    'Rose':      '#D85A30',
    'Provence':  '#D85A30',
    'Global':    '#2C5F8A',
    'Italy':     '#7EC4A5',
    'Spain':     '#F4A261',
    'USA':       '#E07A97',
    'Australia': '#82B1D4',
    'Chile':     '#D4A574',
    'Portugal':  '#E8C170',
    'Germany':   '#9BCFC0',
    'Argentina': '#B8B0C8',
    'Austria':   '#C8B4D6',
    'bg':        '#FAFAF7',
    'grid':      '#E8E6E0',
    'text':      '#3D3D3D',
    'text2':     '#8A8A8A',
}

# ============================================================
# 國名 / 部門 對照
# ============================================================
COUNTRY_ZH = {
    'France': '法國', 'Italy': '義大利', 'Spain': '西班牙',
    'USA': '美國', 'United States': '美國',
    'Australia': '澳洲', 'Chile': '智利', 'Argentina': '阿根廷',
    'South Africa': '南非', 'Portugal': '葡萄牙', 'Germany': '德國',
    'Austria': '奧地利', 'New Zealand': '紐西蘭',
    'United Kingdom': '英國', 'Canada': '加拿大', 'Japan': '日本',
    'China': '中國', 'Netherlands': '荷蘭',
    'China, Hong Kong SAR': '香港', 'Hong Kong': '香港',
    'China, Macao SAR': '澳門', 'Macao': '澳門',
}

DEPT_ZH = {
    '83': 'Var (83)',
    '13': 'BdR (13)',
    '33': 'Bordeaux (33)',
    '34': 'Languedoc (34)',
    '84': 'Vaucluse (84)',
    '11': 'Aude (11)',
    '30': 'Gard (30)',
    '66': 'PO (66)',
    '51': 'Marne (51)',
    '21': "Côte-d'Or (21)",
}

PROVENCE_DEPTS = ['83', '13', '84', '04', '06']

# ============================================================
# 樣式 helper
# ============================================================
def style_axes(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PALETTE['bg'])
    if title:
        ax.set_title(title, fontsize=15, fontweight='bold',
                     color=PALETTE['text'], pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, color=PALETTE['text'])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, color=PALETTE['text'])
    ax.tick_params(colors=PALETTE['text'], labelsize=9)
    ax.grid(True, color=PALETTE['grid'], linestyle='--', alpha=0.7, linewidth=0.7)
    ax.set_axisbelow(True)
    sns.despine(ax=ax)


def add_source_note(fig, source_text):
    fig.text(0.99, 0.01, source_text, ha='right', va='bottom',
             fontsize=8, color=PALETTE['text2'], style='italic')


def save_fig(fig, name, dpi=200):
    if not name.endswith('.png'):
        name += '.png'
    path = os.path.join(FIG_DIR, name)
    fig.patch.set_facecolor(PALETTE['bg'])
    fig.savefig(path, dpi=dpi, bbox_inches='tight',
                facecolor=PALETTE['bg'])
    plt.close(fig)
    print(f"  💾 figures/{name}")


def save_table(df, name):
    if not name.endswith('.csv'):
        name += '.csv'
    path = os.path.join(TBL_DIR, name)
    df.to_csv(path, encoding='utf-8-sig')
    print(f"  📄 tables/{name}")


def get_color(key, default='#999999'):
    return PALETTE.get(key, default)


def country_label(en):
    return COUNTRY_ZH.get(en, en)


def dept_label(code):
    return DEPT_ZH.get(str(code), str(code))


# ============================================================
# 統計工具
# ============================================================
def cagr(start, end, periods):
    """複合年增長率，periods 為期間數（不是年數+1）"""
    if start is None or end is None or start <= 0 or periods <= 0:
        return np.nan
    return (end / start) ** (1.0 / periods) - 1.0


def stars(p):
    """p-value → 顯著符號"""
    if pd.isna(p):
        return ''
    if p < 0.001:
        return '***'
    if p < 0.01:
        return '**'
    if p < 0.05:
        return '*'
    return ''


def welch_t(a, b):
    """Welch's t-test（不等變異）"""
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return {
        'n_a': len(a), 'n_b': len(b),
        'mean_a': np.mean(a), 'mean_b': np.mean(b),
        't': t, 'p': p, 'sig': stars(p),
    }


def mann_whitney(a, b):
    """Mann-Whitney U test"""
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
    return {
        'n_a': len(a), 'n_b': len(b),
        'median_a': np.median(a), 'median_b': np.median(b),
        'U': u, 'p': p, 'sig': stars(p),
    }


def cohen_d(a, b):
    """Cohen's d 效果量（pooled SD）"""
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return np.nan
    pooled = np.sqrt(((na - 1) * np.var(a, ddof=1) +
                      (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    if pooled == 0:
        return np.nan
    return (np.mean(a) - np.mean(b)) / pooled


def rank_biserial(a, b):
    """
    rank-biserial r 效果量（搭配 Mann-Whitney 用）。
    符號慣例：r > 0 表示 a 通常大於 b（與 Cohen's d 同方向，方便閱讀）。
    """
    a = pd.Series(a).dropna().values
    b = pd.Series(b).dropna().values
    if len(a) == 0 or len(b) == 0:
        return np.nan
    u, _ = stats.mannwhitneyu(a, b, alternative='two-sided')
    return (2 * u) / (len(a) * len(b)) - 1


def chi2_test(contingency):
    """卡方獨立性檢定。輸入 2D array / DataFrame"""
    chi2, p, dof, expected = stats.chi2_contingency(contingency)
    n = np.sum(contingency.values if hasattr(contingency, 'values') else contingency)
    cramers_v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1)))
    return {
        'chi2': chi2, 'dof': dof, 'p': p, 'sig': stars(p),
        'cramers_v': cramers_v,
    }


def linear_trend(x, y):
    """線性回歸 trend：回傳 slope, R², p"""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if len(x) < 3:
        return {'slope': np.nan, 'intercept': np.nan, 'r2': np.nan, 'p': np.nan}
    res = stats.linregress(x, y)
    return {
        'slope': res.slope, 'intercept': res.intercept,
        'r2': res.rvalue ** 2, 'p': res.pvalue, 'sig': stars(res.pvalue),
    }
