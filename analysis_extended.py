"""Extended analysis on top of the basic collocates run.

Adds four enrichments beyond the week-4 baseline:

A. Multi-character comparison: 黛玉 vs 宝玉 vs 宝钗 (window h5 each)
   -> output/collocates_baochai_window_h5.csv, collocates_baoyu_window_h5.csv
B. Front/back narrative comparison for 黛玉: chapters 1-80 vs 81-120
   -> output/collocates_daiyu_front80_window_h5.csv / _back40_window_h5.csv
C. Multiple-testing correction (Benjamini-Hochberg) for the 黛玉 runs
   -> output/collocates_daiyu_window_h5_fdr.csv etc.
D. KWIC concordance of 黛玉 from the raw text
   -> output/kwic_daiyu.txt (sampled)
E. Plots: top collocates per run + front/back comparison
   -> output/plot_*.png
"""
import os
import re
import random

import opencc
import jieba
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qhchina import load_stopwords
from qhchina.analytics.collocations import find_collocates

OUT = "output"
os.makedirs(OUT, exist_ok=True)
stopwords = load_stopwords()
BASE_FILTERS = {"stopwords": stopwords, "min_word_length": 2, "max_p": 0.05}

# ------------------------------------------------------------------
# A. load pre-segmented sentences (already simplified + tokenized)
# ------------------------------------------------------------------
sentences = []
with open("data/sentences.txt", encoding="utf-8") as f:
    for line in f:
        tokens = line.split()
        if tokens:
            sentences.append(tokens)
print(f"loaded {len(sentences):,} sentences")

def run(name: str, sents, target: str, **kwargs) -> pd.DataFrame:
    df = find_collocates(
        sentences=sents, target_words=target, filters=BASE_FILTERS,
        sort_by="obs_local", ascending=False, return_type="dataframe", **kwargs)
    path = os.path.join(OUT, f"collocates_{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[run {name}] {len(df)} collocates -> {path}")
    return df

# --- A. multi-character comparison (window h5) ---
daiyu = run("daiyu_window_h5", sentences, "黛玉", method="window", horizon=5)
baoyu = run("baoyu_window_h5", sentences, "宝玉", method="window", horizon=5)
baochai = run("baochai_window_h5", sentences, "宝钗", method="window", horizon=5)

# ------------------------------------------------------------------
# B. front/back split (chapters 1-80 vs 81-120) for 黛玉
#    re-segment with chapter awareness
# ------------------------------------------------------------------
with open("data/hongloumeng.txt", encoding="utf-8") as f:
    raw = f.read()
raw = opencc.OpenCC("t2s").convert(raw)

chap_pat = re.compile(r"第[零一二三四五六七八九十百廿\d]+回[^\n]*")
heads = list(chap_pat.finditer(raw))
print(f"chapter headings: {len(heads)}")

def seg_chunk(chunk: str) -> list[list[str]]:
    out = []
    for s in re.split(r"[。！？]+", chunk):
        words = [w for w in jieba.lcut(s)
                 if re.fullmatch(r"[\u4e00-\u9fff\u3400-\u4dbf0-9A-Za-z]+", w)]
        if len(words) >= 5:
            out.append(words)
    return out

def ch2num(h: str) -> int:
    m = re.match(r"第([零一二三四五六七八九十百廿\d]+)回", h)
    t = m.group(1)
    digits = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
    if t.isdigit():
        return int(t)
    # chinese numeral -> int (handles up to 120)
    total, num = 0, 0
    for ch in t:
        if ch in digits:
            num = digits[ch]
        elif ch == "十":
            total += (num or 1) * 10
            num = 0
        elif ch == "百":
            total += (num or 1) * 100
            num = 0
        elif ch == "廿":
            total += 20
            num = 0
    return total + num

front, back = [], []
for i, m in enumerate(heads):
    end = heads[i + 1].start() if i + 1 < len(heads) else len(raw)
    body = seg_chunk(raw[m.start():end])
    (front if ch2num(m.group(0)) <= 80 else back).extend(body)
print(f"front(1-80): {len(front):,} sents | back(81-120): {len(back):,} sents")

daiyu_front = run("daiyu_front80_window_h5", front, "黛玉", method="window", horizon=5)
daiyu_back = run("daiyu_back40_window_h5", back, "黛玉", method="window", horizon=5)

# ------------------------------------------------------------------
# C. FDR (Benjamini-Hochberg) corrected versions of the three baseline runs
# ------------------------------------------------------------------
for name, kw in [("daiyu_window_h5", dict(method="window", horizon=5)),
                 ("daiyu_window_h10", dict(method="window", horizon=10)),
                 ("daiyu_sentence", dict(method="sentence"))]:
    df = find_collocates(
        sentences=sentences, target_words="黛玉", filters=BASE_FILTERS,
        correction="fdr_bh", sort_by="obs_local", ascending=False,
        return_type="dataframe", **kw)
    path = os.path.join(OUT, f"collocates_{name}_fdr.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    sig = int((df["adjusted_p_value"] < 0.05).sum())
    print(f"[fdr {name}] {len(df)} rows, {sig} survive adjusted p<0.05 -> {path}")

# ------------------------------------------------------------------
# D. KWIC concordance of 黛玉 from the simplified raw text (sampled)
# ------------------------------------------------------------------
random.seed(42)
hits = [m.start() for m in re.finditer("黛玉", raw)]
sample = random.sample(hits, min(60, len(hits)))
lines = [f"KWIC concordance for 黛玉 (sampling {len(sample)} of {len(hits)} occurrences, ±30 chars)", "=" * 70]
for pos in sorted(sample):
    ctx = raw[max(0, pos - 30):pos + 32].replace("\n", " ").replace("\r", " ")
    lines.append(ctx)
with open(os.path.join(OUT, "kwic_daiyu.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"[kwic] {len(sample)} lines -> {OUT}/kwic_daiyu.txt")

# ------------------------------------------------------------------
# E. Plots (Chinese font for Windows)
# ------------------------------------------------------------------
plt.rcParams["font.family"] = ["Microsoft JhengHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

def bar_top(df: pd.DataFrame, title: str, fname: str, n: int = 15,
            value: str = "obs_local") -> None:
    top = df.head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(top["collocate"], top[value], color="#8b3a3a")
    ax.set_xlabel({"obs_local": "obs_local（共现次数）",
                   "ratio_local": "ratio_local（obs/exp）"}[value])
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)
    print(f"[plot] {fname}")

bar_top(daiyu, "黛玉 搭配词 top 15（window, horizon=5）", "plot_daiyu_h5_top15.png")
bar_top(daiyu, "黛玉 搭配词 top 15（window, horizon=10）", "plot_daiyu_h10_top15.png")
bar_top(daiyu, "黛玉 搭配词 top 15（sentence 法）", "plot_daiyu_sentence_top15.png")
bar_top(daiyu, "黛玉 搭配词 top 15（obs/exp 比，obs≥10）", "plot_daiyu_ratio_top15.png",
        n=15, value="ratio_local")

# three-character comparison: shared vs unique among each one's top-50
sets = {"黛玉": set(daiyu.head(50)["collocate"]),
        "宝玉": set(baoyu.head(50)["collocate"]),
        "宝钗": set(baochai.head(50)["collocate"])}
allw = sorted(set().union(*sets.values()))
presence = pd.DataFrame({k: [1 if w in s else 0 for w in allw] for k, s in sets.items()},
                        index=allw)
order = presence.sum(axis=1).sort_values(ascending=False)
presence = presence.loc[order.index[:30]]
fig, ax = plt.subplots(figsize=(8, 9))
ax.imshow(presence.values, cmap="Reds", aspect="auto", vmin=0, vmax=3)
ax.set_xticks(range(3), presence.columns)
ax.set_yticks(range(len(presence)), presence.index)
for i, w in enumerate(presence.index):
    for j, k in enumerate(presence.columns):
        if presence.iloc[i, j]:
            ax.text(j, i, "●", ha="center", va="center", fontsize=8)
ax.set_title("三大角色 top-50 搭配词的重叠（前 30 词）")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "plot_three_chars_overlap.png"), dpi=150)
plt.close(fig)
print("[plot] plot_three_chars_overlap.png")

# front/back comparison: top-15 ranks side by side
fb = pd.DataFrame({
    "front(1-80)": daiyu_front.head(15)["collocate"].tolist(),
    "back(81-120)": daiyu_back.head(15)["collocate"].tolist(),
})
fig, ax = plt.subplots(figsize=(6, 7))
ax.axis("off")
tbl = ax.table(cellText=fb.values, colLabels=fb.columns, loc="center",
               cellLoc="center")
tbl.scale(1, 1.6)
ax.set_title("黛玉搭配词 top 15：前 80 回 vs 后 40 回（window h5）", pad=20)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "plot_daiyu_front_back.png"), dpi=150)
plt.close(fig)
print("[plot] plot_daiyu_front_back.png")

# quick text summary of the front/back difference for the report
only_front = set(daiyu_front.head(30)["collocate"]) - set(daiyu_back.head(30)["collocate"])
only_back = set(daiyu_back.head(30)["collocate"]) - set(daiyu_front.head(30)["collocate"])
with open(os.path.join(OUT, "front_back_notes.txt"), "w", encoding="utf-8") as f:
    f.write(f"front80 sents={len(front)} back40 sents={len(back)}\n")
    f.write(f"黛玉 in front: obs_global sum n/a; front top30-only: {', '.join(sorted(only_front))}\n")
    f.write(f"back top30-only: {', '.join(sorted(only_back))}\n\n")
    f.write("front top15:\n" + "\n".join(daiyu_front.head(15)[["collocate","obs_local","ratio_local"]].astype(str).agg(" ".join, axis=1)) + "\n\n")
    f.write("back top15:\n" + "\n".join(daiyu_back.head(15)[["collocate","obs_local","ratio_local"]].astype(str).agg(" ".join, axis=1)) + "\n\n")
    f.write("three-char top10 side by side\n")
    f.write(pd.DataFrame({"黛玉": daiyu.head(10)["collocate"].tolist(),
                          "宝玉": baoyu.head(10)["collocate"].tolist(),
                          "宝钗": baochai.head(10)["collocate"].tolist()}).to_string())
print("[notes] front_back_notes.txt")