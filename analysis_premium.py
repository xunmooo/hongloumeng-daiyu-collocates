"""Premium analyses: narrative attention curves, collocate network,
association-measure comparison, and name-variant robustness.

A. Character-space curves: per-chapter share of narrative attention
   (tokens of 黛玉/宝玉/宝钗/紫鹃 / all tokens) -> Woloch quantified
   -> output/character_space_by_chapter.csv, output/plot_char_space_curves.png
B. Collocate network of 黛玉 (window h5, top 25)
   -> output/plot_daiyu_network.png
C. Association-measure comparison: same run sorted by log_dice with
   t_score & log_likelihood columns
   -> output/collocates_daiyu_window_h5_measures.csv
D. Name-variant robustness: pooled target {黛玉, 林黛玉}
   -> output/collocates_daiyu_pooled_h5.csv + overlap note
"""
import os
import re

import jieba
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from qhchina import load_stopwords
from qhchina.analytics.collocations import find_collocates

from chapter_split import load_chapters

OUT = "output"
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = ["Microsoft JhengHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

stopwords = load_stopwords()
BASE_FILTERS = {"stopwords": stopwords, "min_word_length": 2, "max_p": 0.05}

# base run for B/C/D comparisons
sentences = []
with open("data/sentences.txt", encoding="utf-8") as f:
    for line in f:
        toks = line.split()
        if toks:
            sentences.append(toks)
print(f"loaded {len(sentences):,} sentences")

daiyu_h5 = find_collocates(
    sentences=sentences, target_words="黛玉", method="window", horizon=5,
    filters=BASE_FILTERS, sort_by="obs_local", ascending=False,
    return_type="dataframe")

# ------------------------------------------------------------------
# A. per-chapter character-space curves
# ------------------------------------------------------------------
word_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf0-9A-Za-z]+")

TARGETS = ["黛玉", "宝玉", "宝钗", "紫鹃"]
rows = []
chapters = load_chapters()
for num, body in chapters.items():
    words = [w for w in jieba.lcut(body) if word_re.fullmatch(w)]
    n = len(words)
    cnt = {t: sum(1 for w in words if w == t) for t in TARGETS}
    rows.append({"chapter": num, "n_words": n,
                 **{f"{t}_tokens": cnt[t] for t in TARGETS},
                 **{f"{t}_share": cnt[t] / n * 100 for t in TARGETS}})
cs = pd.DataFrame(rows)
cs.to_csv(os.path.join(OUT, "character_space_by_chapter.csv"),
          index=False, encoding="utf-8-sig")
print(f"[curves] {len(cs)} chapters -> character_space_by_chapter.csv")

fig, ax = plt.subplots(figsize=(11, 5))
colors = {"黛玉": "#8b2f2f", "宝玉": "#3f5c54", "宝钗": "#b08d4f", "紫鹃": "#5d7aa3"}
for t in TARGETS:
    y = cs[f"{t}_share"].rolling(3, center=True, min_periods=1).mean()
    ax.plot(cs["chapter"], y, label=t, color=colors[t],
            lw=2.4 if t == "黛玉" else 1.5, alpha=1.0 if t == "黛玉" else .8)
ax.axvline(80, color="#999", ls="--", lw=1)
ax.text(80.5, ax.get_ylim()[1] * .92, "第 80 回（程高本續書分界）", fontsize=9, color="#666")
ax.annotate("第 97–98 回\n焚稿・魂归", xy=(97.5, cs[cs.chapter.between(95, 100)]["黛玉_share"].max()),
            fontsize=9, color="#8b2f2f", ha="center",
            arrowprops=dict(arrowstyle="->", color="#8b2f2f", lw=1))
ax.set_xlabel("章回")
ax.set_ylabel("人物空間份額（%）— 該角色詞頻 / 全章詞數")
ax.set_title("敘事注意力的分配：《紅樓夢》各回中四位角色的人物空間份額")
ax.legend(loc="upper right")
ax.set_xlim(1, 120)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "plot_char_space_curves.png"), dpi=150)
plt.close(fig)
print("[plot] plot_char_space_curves.png")

# ------------------------------------------------------------------
# B. collocate network (top 25 by obs_local)
# ------------------------------------------------------------------
top = daiyu_h5.head(25)
G = nx.Graph()
G.add_node("黛玉", kind="target", freq=daiyu_h5["obs_local"].max())
for _, r in top.iterrows():
    G.add_edge("黛玉", r["collocate"], weight=float(r["obs_local"]))
    G.add_node(r["collocate"], kind="collocate", freq=float(r["obs_global"]))

pos = nx.spring_layout(G, k=0.85, seed=11, weight="weight")
sizes = [900 if d["kind"] == "target" else 120 + 90 * np.sqrt(d["freq"])
         for _, d in G.nodes(data=True)]
ncolors = ["#8b2f2f" if d["kind"] == "target" else "#3f5c54"
           for _, d in G.nodes(data=True)]
ewidths = [0.6 + G[u][v]["weight"] / max(d["weight"] for _, _, d in G.edges(data=True)) * 4
           for u, v in G.edges()]
fig, ax = plt.subplots(figsize=(9.5, 9.5))
nx.draw_networkx_edges(G, pos, ax=ax, width=ewidths, edge_color="#b08d4f", alpha=.45)
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color=ncolors, alpha=.88)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=10,
                        font_family="Microsoft JhengHei")
ax.set_title("黛玉的搭配詞網絡（window h5，top 25；節點大小＝全書詞頻，邊寬＝共現次數）",
             fontsize=11)
ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "plot_daiyu_network.png"), dpi=150)
plt.close(fig)
print("[plot] plot_daiyu_network.png")

# ------------------------------------------------------------------
# C. association-measure comparison (same counts, different rankings)
# ------------------------------------------------------------------
meas = find_collocates(
    sentences=sentences, target_words="黛玉", method="window", horizon=5,
    filters=BASE_FILTERS,
    measures=["log_dice", "t_score", "log_likelihood"],
    sort_by="log_dice", ascending=False, return_type="dataframe")
meas.to_csv(os.path.join(OUT, "collocates_daiyu_window_h5_measures.csv"),
            index=False, encoding="utf-8-sig")
print(f"[measures] {len(meas)} rows -> collocates_daiyu_window_h5_measures.csv")

# ------------------------------------------------------------------
# D. name-variant robustness: pooled {黛玉, 林黛玉}
# ------------------------------------------------------------------
pooled = find_collocates(
    sentences=sentences, target_words=["黛玉", "林黛玉"], pooled=True,
    method="window", horizon=5, filters=BASE_FILTERS,
    sort_by="obs_local", ascending=False, return_type="dataframe")
pooled.to_csv(os.path.join(OUT, "collocates_daiyu_pooled_h5.csv"),
              index=False, encoding="utf-8-sig")
print(f"[pooled] {len(pooled)} rows -> collocates_daiyu_pooled_h5.csv")

a = set(daiyu_h5.head(50)["collocate"])
b = set(pooled.head(50)["collocate"])
with open(os.path.join(OUT, "pooled_overlap_note.txt"), "w", encoding="utf-8") as f:
    f.write(f"top-50 overlap between 黛玉-only and pooled(黛玉+林黛玉): "
            f"{len(a & b)}/50\n")
    f.write(f"only in pooled top-50: {', '.join(sorted(b - a))}\n")
    f.write(f"only in 黛玉-only top-50: {', '.join(sorted(a - b))}\n")
print("[note] pooled_overlap_note.txt:", f"overlap {len(a & b)}/50")