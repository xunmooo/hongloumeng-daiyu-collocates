"""Build output/results.html: a single themed page integrating ALL collocate
CSV files in output/ for side-by-side comparison (week-4 lecture, prompt 3),
extended with overview stats, a quick top-15 comparison view, KWIC excerpts,
plots, and a methods footer.
"""
import glob
import html
import os
import re

import pandas as pd

OUT_DIR = "output"
CSV_PATTERN = os.path.join(OUT_DIR, "collocates_*.csv")

PRETTY = {
    "daiyu_window_h5": "黛玉 · 視窗法 horizon=5",
    "daiyu_window_h10": "黛玉 · 視窗法 horizon=10",
    "daiyu_sentence": "黛玉 · 句子法（同句共現）",
    "baoyu_window_h5": "宝玉 · 視窗法 horizon=5（對照組）",
    "baochai_window_h5": "宝钗 · 視窗法 horizon=5（對照組）",
    "daiyu_front80_window_h5": "黛玉 · 前 80 回（horizon=5）",
    "daiyu_back40_window_h5": "黛玉 · 後 40 回（horizon=5）",
    "daiyu_window_h5_fdr": "黛玉 · 視窗 h5 · FDR 校正",
    "daiyu_window_h10_fdr": "黛玉 · 視窗 h10 · FDR 校正",
    "daiyu_sentence_fdr": "黛玉 · 句子法 · FDR 校正",
}
NUM_COLS = {"exp_local", "ratio_local", "obs_global", "p_value",
            "adjusted_p_value", "log_likelihood", "log_dice", "t_score", "mi"}
COL_NOTES = {
    "collocate": "搭配詞",
    "obs_local": "實際共現次數（O）",
    "exp_local": "隨機期望共現（E）",
    "ratio_local": "obs／exp 比",
    "obs_global": "全書出現次數",
    "p_value": "Fisher 精確檢定 p 值",
    "adjusted_p_value": "FDR 校正後 p 值",
    "target": "目標詞",
}

GROUPS = [
    ("基礎三設定（講義要求）",
     ["collocates_daiyu_window_h5", "collocates_daiyu_window_h10", "collocates_daiyu_sentence"]),
    ("多角色對照：黛玉・宝玉・宝钗",
     ["collocates_baoyu_window_h5", "collocates_baochai_window_h5"]),
    ("敘事時間：前 80 回 vs 後 40 回",
     ["collocates_daiyu_front80_window_h5", "collocates_daiyu_back40_window_h5"]),
    ("FDR 多重檢定校正版",
     ["collocates_daiyu_window_h5_fdr", "collocates_daiyu_window_h10_fdr", "collocates_daiyu_sentence_fdr"]),
]

def label_of(stem: str) -> str:
    return PRETTY.get(stem, stem)

def load_tables() -> dict[str, dict]:
    tables = {}
    for path in sorted(glob.glob(CSV_PATTERN)):
        stem = os.path.splitext(os.path.basename(path))[0]
        tables[stem] = {"id": stem, "label": label_of(stem),
                        "df": pd.read_csv(path), "csv": os.path.basename(path)}
    return tables

def fmt_cell(col: str, v) -> str:
    if pd.isna(v):
        return "—"
    if col in ("p_value", "adjusted_p_value"):
        return f"{v:.3g}"
    if col in ("exp_local", "ratio_local"):
        return f"{v:.3g}"
    if col in ("obs_local", "obs_global"):
        return f"{int(v):,}"
    return html.escape(str(v))

def render_table(tab: dict, max_rows: int | None = None) -> str:
    df = tab["df"]
    if "adjusted_p_value" in df.columns:
        cols = [c for c in df.columns if c != "adjusted_p_value"]
        cols.insert(cols.index("p_value") + 1, "adjusted_p_value")
        df = df[cols]
    n = len(df)
    shown = df if max_rows is None else df.head(max_rows)
    head = "".join(f'<th title="{html.escape(COL_NOTES.get(c, c))}">{html.escape(c)}</th>'
                   for c in df.columns)
    rows = []
    for _, r in shown.iterrows():
        cells = []
        for col in df.columns:
            v = r[col]
            if col == "collocate":
                text = f'<strong>{html.escape(str(v))}</strong>'
            elif col in NUM_COLS:
                text = fmt_cell(col, v)
            else:
                text = html.escape(str(v))
            cells.append(f"<td>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    note = "" if max_rows is None or n <= max_rows else \
        f'<p class="meta">⋯ 共 {n:,} 列，僅顯示前 {max_rows} 列（完整資料見 CSV）</p>'
    return (f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{note}')

def side_by_side(tables: dict, ids: list[str], n: int = 15) -> str:
    """Rank-order quick comparison: top-n words of each run, with obs bars."""
    runs = [(tables[i]["label"].split(" · ")[0], tables[i]["df"].head(n)) for i in ids]
    max_obs = max(df["obs_local"].max() for _, df in runs)
    cols = []
    for name, df in runs:
        items = []
        for _, r in df.iterrows():
            w, obs = r["collocate"], int(r["obs_local"])
            width = max(4, round(obs / max_obs * 100))
            items.append(
                f'<li><span class="w">{html.escape(w)}</span>'
                f'<span class="bar"><i style="width:{width}%"></i></span>'
                f'<span class="n">{obs:,}</span></li>')
        cols.append(f'<div class="sbs-col"><h4>{html.escape(name)}</h4><ol>{"".join(items)}</ol></div>')
    return f'<div class="sbs">{"".join(cols)}</div>'

def render_kwic(path: str, limit: int = 24) -> str:
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln and not ln.startswith("KWIC")][1:]
    sample = lines[:: max(1, len(lines) // limit)][:limit]
    lis = "".join(f"<li>{html.escape(ln).replace('黛玉', '<mark>黛玉</mark>')}</li>"
                  for ln in sample)
    return f'<ol class="kwic">{lis}</ol>'

def render_stats() -> str:
    with open("data/hongloumeng.txt", encoding="utf-8") as f:
        chars = len(f.read())
    with open("data/sentences.txt", encoding="utf-8") as f:
        lines = f.read().splitlines()
    tokens = sum(len(ln.split()) for ln in lines)
    daiyu = sum(1 for ln in lines for w in ln.split() if w == "黛玉")
    cards = [
        ("語料", "《紅樓夢》120 回"),
        ("字數", f"{chars:,}"),
        ("句子（≥5詞）", f"{len(lines):,}"),
        ("詞數", f"{tokens:,}"),
        ("目標詞「黛玉」", f"{daiyu:,} 次"),
    ]
    return '<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{html.escape(k)}</div><div class="v">{html.escape(v)}</div></div>'
        for k, v in cards) + "</div>"

def main() -> None:
    tables = load_tables()
    if not tables:
        raise SystemExit(f"no CSV files matching {CSV_PATTERN} — run collocates.py first")

    # ---------- quick comparison (base three runs) ----------
    base_ids = ["collocates_daiyu_window_h5", "collocates_daiyu_window_h10", "collocates_daiyu_sentence"]
    quick = ""
    if all(i in tables for i in base_ids):
        quick = (f'<h2><span class="sec-no">一</span>三種設定速覽（top 15，依 obs_local）</h2>'
                 f'<p class="meta">同一目標詞在三種「鄰近」定義下的搭配詞排行；橫條長度＝obs_local 相對大小。'
                 f'完整表見下方第二節。</p>{side_by_side(tables, base_ids)}')

    # ---------- grouped tables ----------
    sections = []
    for gi, (gtitle, ids) in enumerate(GROUPS, start=2):
        avail = [i for i in ids if i in tables]
        if not avail:
            continue
        parts = [f'<h2><span class="sec-no">{chr(64+gi)}</span>{html.escape(gtitle)}</h2>']
        for t_id in avail:
            t = tables[t_id]
            n = len(t["df"])
            max_p = t["df"]["p_value"].max()
            parts.append(
                f'<details open class="tbl"><summary>{html.escape(t["label"])}'
                f'<span class="badge">{n:,} 搭配詞 · max p = {max_p:.3g}</span></summary>'
                f'<p class="meta"><a href="{t["csv"]}" download>⤓ 下載此表 CSV</a></p>'
                + render_table(t) + "</details>")
        sections.append("".join(parts))
    section_html = "".join(sections)

    # ---------- plots ----------
    plots = sorted(glob.glob(os.path.join(OUT_DIR, "plot_*.png")))
    plot_caps = {
        "plot_daiyu_h5_top15": "黛玉 top 15 搭配詞（視窗 h5）",
        "plot_daiyu_h10_top15": "黛玉 top 15 搭配詞（視窗 h10）",
        "plot_daiyu_sentence_top15": "黛玉 top 15 搭配詞（句子法）",
        "plot_daiyu_ratio_top15": "黛玉 top 15（obs/exp 比，obs≥10）——最「排他」的搭配詞",
        "plot_three_chars_overlap": "三角色 top-50 搭配詞重疊矩陣",
        "plot_daiyu_front_back": "前 80 回 vs 後 40 回 top 15 對照",
    }
    gallery = ""
    if plots:
        figs = "".join(
            f'<figure><img src="{os.path.basename(p)}" loading="lazy" alt="{os.path.basename(p)}">'
            f'<figcaption>{html.escape(plot_caps.get(os.path.splitext(os.path.basename(p))[0], os.path.basename(p)))}</figcaption></figure>'
            for p in plots)
        gallery = f'<h2><span class="sec-no">五</span>圖表</h2><div class="gallery">{figs}</div>'

    # ---------- kwic ----------
    kwic_html = ""
    kwic_path = os.path.join(OUT_DIR, "kwic_daiyu.txt")
    if os.path.exists(kwic_path):
        kwic_html = (f'<h2><span class="sec-no">六</span>KWIC 脈絡例句（抽樣）</h2>'
                     f'<p class="meta">自原文抽樣黛玉出現處（±30 字）；完整清單見 <code>output/kwic_daiyu.txt</code>。</p>'
                     + render_kwic(kwic_path))

    stats = render_stats()

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>滿紙荒唐言・誰解其中味——黛玉的搭配詞與人物空間</title>
<style>
  :root {{
    --paper: #f6efe0; --ink: #3a2e2a; --faint: #7a6a5c;
    --jiang: #8b2f2f; --dai: #3f5c54; --line: #d9c9a8; --gold: #b08d4f;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
    background: var(--paper); color: var(--ink); margin: 0;
    background-image: repeating-linear-gradient(0deg, transparent 0 27px, rgba(176,141,79,.06) 27px 28px);
  }}
  .wrap {{ max-width: 1150px; margin: 0 auto; padding: 0 1.2rem 4rem; }}
  header.banner {{
    text-align: center; padding: 2.6rem 1rem 1.8rem; border-bottom: 3px double var(--line);
    margin-bottom: 1.6rem;
  }}
  header.banner h1 {{
    font-family: "Kaiti TC", "DFKai-SB", KaiTi, "STKaiti", serif;
    font-size: 2rem; letter-spacing: .12em; margin: .2rem 0; color: var(--jiang);
  }}
  header.banner .sub {{ color: var(--faint); letter-spacing: .08em; font-size: .95rem; }}
  header.banner .seal {{
    display: inline-block; border: 2px solid var(--jiang); color: var(--jiang);
    font-family: "Kaiti TC", "DFKai-SB", KaiTi, serif; padding: .1rem .5rem;
    border-radius: 4px; font-size: .9rem; letter-spacing: .3em; margin-top: .6rem;
  }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .8rem; margin: 1.4rem 0; }}
  .card {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px;
          padding: .8rem .9rem; text-align: center; box-shadow: 0 1px 3px rgba(90,60,30,.08); }}
  .card .k {{ font-size: .8rem; color: var(--faint); letter-spacing: .06em; }}
  .card .v {{ font-size: 1.25rem; font-weight: 700; color: var(--dai); margin-top: .2rem; }}
  h2 {{ font-family: "Kaiti TC", "DFKai-SB", KaiTi, serif; color: var(--jiang);
       border-bottom: 1px solid var(--line); padding-bottom: .35rem; margin-top: 2.6rem;
       font-size: 1.35rem; letter-spacing: .06em; }}
  .sec-no {{ display: inline-block; background: var(--jiang); color: #fff; font-size: .8rem;
           width: 1.6em; height: 1.6em; line-height: 1.6em; text-align: center;
           border-radius: 50%; margin-right: .5rem; vertical-align: 2px; }}
  .meta {{ color: var(--faint); font-size: .88rem; }}
  code {{ background: #efe6d2; padding: 0 .3em; border-radius: 4px; font-size: .85em; }}
  details.tbl {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px;
               margin: 1rem 0; padding: .6rem .9rem; box-shadow: 0 1px 3px rgba(90,60,30,.08); }}
  details.tbl summary {{ cursor: pointer; font-weight: 700; color: var(--dai); font-size: 1.02rem; }}
  .badge {{ font-weight: 400; font-size: .78rem; color: var(--faint); margin-left: .6rem;
          border: 1px solid var(--line); padding: .05rem .5rem; border-radius: 99px; }}
  .table-wrap {{ overflow-x: auto; max-height: 480px; margin-top: .7rem; border: 1px solid var(--line); }}
  table {{ border-collapse: collapse; font-size: .9rem; width: 100%; }}
  th, td {{ border: 1px solid #e3d7bd; padding: .3rem .55rem; text-align: right; white-space: nowrap; }}
  th:first-child, td:first-child {{ text-align: left; }}
  thead th {{ background: var(--dai); color: #f6efe0; position: sticky; top: 0; font-weight: 600; }}
  tbody tr:nth-child(even) {{ background: #f7f2e4; }}
  tbody tr:hover {{ background: #efe4c8; }}
  /* side-by-side quick view */
  .sbs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
  .sbs-col {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px; padding: .7rem 1rem; }}
  .sbs-col h4 {{ margin: .1rem 0 .6rem; color: var(--dai); font-size: .98rem; }}
  .sbs-col ol {{ list-style: none; margin: 0; padding: 0; counter-reset: rk; }}
  .sbs-col li {{ display: grid; grid-template-columns: 3.4em 1fr 3.6em; align-items: center;
               gap: .5rem; padding: .12rem 0; counter-increment: rk; font-size: .95rem; }}
  .sbs-col li::before {{ content: counter(rk); color: var(--gold); font-variant-numeric: tabular-nums;
                       text-align: right; }}
  .sbs-col .w {{ font-weight: 700; }}
  .sbs-col .bar {{ background: #ece2c8; border-radius: 3px; height: .8em; overflow: hidden; }}
  .sbs-col .bar i {{ display: block; height: 100%; background: linear-gradient(90deg, var(--dai), var(--jiang)); }}
  .sbs-col .n {{ color: var(--faint); font-size: .82rem; text-align: right; font-variant-numeric: tabular-nums; }}
  /* kwic */
  ol.kwic {{ list-style: none; padding: 0; columns: 2; column-gap: 2rem; font-size: .92rem; }}
  ol.kwic li {{ margin: 0 0 .45rem; padding: .35rem .6rem; background: #fffdf6;
              border: 1px solid var(--line); border-radius: 6px; break-inside: avoid; }}
  ol.kwic mark {{ background: #f3d9c8; color: var(--jiang); font-weight: 700; padding: 0 .15em; border-radius: 3px; }}
  /* gallery */
  .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }}
  figure {{ margin: 0; border: 1px solid var(--line); padding: .6rem; background: #fffdf6;
          border-radius: 10px; }}
  figure img {{ max-width: 100%; display: block; margin: 0 auto; }}
  figcaption {{ font-size: .82rem; color: var(--faint); margin-top: .5rem; text-align: center; }}
  footer.methods {{ margin-top: 3rem; border-top: 3px double var(--line); padding-top: 1.2rem;
                  font-size: .88rem; color: var(--faint); }}
  footer.methods dt {{ font-weight: 700; color: var(--dai); }}
  footer.methods dd {{ margin: 0 0 .5rem 1.2em; }}
</style>
</head>
<body>
<div class="wrap">
<header class="banner">
  <div class="sub">搭配詞分析 × Woloch 人物空間</div>
  <h1>瀟湘館裡的詞與人</h1>
  <div class="sub">《紅樓夢》一百二十回・目標詞「黛玉」</div>
  <div class="seal">石頭記</div>
</header>
{stats}
{quick}
{section_html}
{gallery}
{kwic_html}
<footer class="methods">
  <h2>方法註記</h2>
  <dl>
    <dt>流程</dt><dd>opencc 繁→簡（本語料已為簡體，轉換為 no-op）→ 中文句末標點分句（。！？）→ jieba 分詞 → 移除標點 → 保留 ≥5 詞的句子。</dd>
    <dt>停用詞</dt><dd>qhchina.load_stopwords()（預設 zh_sim，806 詞），經 filters 傳入。</dd>
    <dt>統計</dt><dd>qhchina.analytics.collocations.find_collocates；每個搭配詞對 2×2 列聯表（Evert 2008）做 Fisher 精確檢定，alternative="greater"（檢定共現高於隨機預期）。</dd>
    <dt>filters</dt><dd>min_word_length=2（聚焦雙字詞以上）、max_p=0.05（表中每一列 p &lt; 0.05）、stopwords。</dd>
    <dt>三種設定</dt><dd>window horizon=5（左右各5詞）、window horizon=10、sentence（同一句）。FDR 版另附 Benjamini–Hochberg adjusted_p_value。</dd>
    <dt>欄位</dt><dd>obs_local＝實際共現；exp_local＝隨機期望；ratio_local＝obs/exp；obs_global＝搭配詞全書頻率；p_value＝Fisher 精確檢定。</dd>
  </dl>
</footer>
</div>
</body>
</html>"""
    out = os.path.join(OUT_DIR, "results.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"written {out}: {len(tables)} tables, {len(plots)} plots")

if __name__ == "__main__":
    main()