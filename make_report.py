"""Build output/results.html: a themed single page integrating ALL collocate
CSVs in output/ for side-by-side comparison (week-4 lecture, prompt 3),
plus premium sections: character-space curves, collocate network,
association-measure comparison, name-variant check, KWIC excerpts,
a literary glossary, and a methods footer.
"""
import glob
import html
import os

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
    "daiyu_window_h5_measures": "黛玉 · 視窗 h5 · 依 logDice 排序",
    "daiyu_pooled_h5": "黛玉 · 併集目標（黛玉＋林黛玉）horizon=5",
}
NUM_COLS = {"exp_local", "ratio_local", "obs_global", "p_value",
            "adjusted_p_value", "log_likelihood", "log_dice", "t_score", "mi"}
COL_NOTES = {
    "collocate": "搭配詞",
    "obs_local": "實際共現次數（O11）",
    "exp_local": "隨機期望共現（E11）",
    "ratio_local": "obs／exp 比（>1 為吸引）",
    "obs_global": "搭配詞全書頻率",
    "p_value": "Fisher 精確檢定 p 值",
    "adjusted_p_value": "FDR 校正後 p 值",
    "log_dice": "logDice（2·f(A,B)/(f(A)+f(B))）",
    "t_score": "t-score（O11−E11)/√O11",
    "log_likelihood": "對數似然比 G²",
    "target": "目標詞",
}

GLOSSARY = {
    "紫鹃": "黛玉的貼身丫鬟（本為賈母之婢鸚哥，黛玉入府後賈母將她撥給黛玉）。黛玉殁後送靈南下、後隨惜春出家——搭配詞 obs/exp 比最高者，人物空間最排他。",
    "雪雁": "黛玉自蘇州家中帶來的小丫鬟。視窗擴大到 10 詞才躍升、後40回回升——一個「半徑擴大才浮現」的次要角色。",
    "宝玉": "賈寶玉。與黛玉為「木石前盟」；三種設定下穩居第一的搭配詞。",
    "宝钗": "薛寶釵。「金玉良緣」的另一方。obs/exp 比 5–13，是黛玉空間裡最主要的「他者」。",
    "湘云": "史湘雲，賈母姪孫女。海棠詩社中與黛玉聯句、亦曾口角，關係的雙面性在搭配詞中可見。",
    "探春": "賈探春，三小姐，海棠詩社發起人——詩社場景把黛玉與探春綁在一起。",
    "潇湘": "瀟湘館，黛玉在大觀園的居所；詩號「瀟湘妃子」典出娥皇女英哭竹，暗含「淚」的主題。",
    "贾母": "外祖母，黛玉入府後的庇護者。視窗 h5 顯著、h10 消失——賈母出場於社交場合，多在稍遠的敘事距離。",
    "王夫人": "寶玉之母、黛玉舅母。僅在句子法中顯著——屬於禮節性同場，而非身體鄰近。",
    "眼泪": "「還淚」神話：絳珠仙草以一生眼淚償神瑛侍者灌溉之恩。黛玉的人物空間幾乎由淚定義。",
    "心中": "敘述者進入人物內心的標記——黛玉段落的心理描寫密度高於其他角色。",
    "光景": "神情、樣子。後40回才進入 top15，續書敘述風格趨平實的痕跡。",
    "点点头": "後40回 obs/exp 比高達 19——病中虛弱的身體動作取代了前80回的機鋒言語。",
    "冷笑": "前80回黛玉的標誌性動作（機鋒、尖刻），後40回消失。",
    "只见": "話本敘事套語，引入視野所見——說明黛玉常作為視覺焦點出場。",
    "一面": "「一面……一面……」連動句式，敘事節奏的痕跡。",
}

GROUPS = [
    ("basic", "基礎三設定（第 4 週講義要求）",
     ["collocates_daiyu_window_h5", "collocates_daiyu_window_h10", "collocates_daiyu_sentence"]),
    ("chars", "多角色對照：黛玉・宝玉・宝钗",
     ["collocates_baoyu_window_h5", "collocates_baochai_window_h5"]),
    ("time", "敘事時間：前 80 回 vs 後 40 回",
     ["collocates_daiyu_front80_window_h5", "collocates_daiyu_back40_window_h5"]),
    ("names", "名稱變體檢核：併集目標（黛玉＋林黛玉）",
     ["collocates_daiyu_pooled_h5"]),
    ("fdr", "FDR 多重檢定校正版（Benjamini–Hochberg）",
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
    if col in ("exp_local", "ratio_local", "log_dice", "t_score", "log_likelihood"):
        return f"{v:.3g}"
    if col in ("obs_local", "obs_global"):
        return f"{int(v):,}"
    return html.escape(str(v))

def render_table(tab: dict, table_id: str) -> str:
    df = tab["df"]
    if "adjusted_p_value" in df.columns:
        cols = [c for c in df.columns if c != "adjusted_p_value"]
        cols.insert(cols.index("p_value") + 1, "adjusted_p_value")
        df = df[cols]
    head = "".join(f'<th title="{html.escape(COL_NOTES.get(c, c))}">{html.escape(c)}</th>'
                   for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for col in df.columns:
            v = r[col]
            if col == "collocate":
                w = str(v)
                tip = GLOSSARY.get(w)
                tipattr = f' title="{html.escape(tip)}"' if tip else ""
                text = f'<strong{tipattr}>{html.escape(w)}</strong>'
            elif col in NUM_COLS:
                text = fmt_cell(col, v)
            else:
                text = html.escape(str(v))
            cells.append(f"<td>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<input class="tbl-search" data-tbl="{table_id}" placeholder="搜尋搭配詞…">'
            f'<div class="table-wrap" id="{table_id}"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')

def rank_list(df: pd.DataFrame, value: str, n: int, label: str, fmt: str) -> str:
    df = df.sort_values(value, ascending=False).head(n)
    vmax = df[value].max()
    items = []
    for _, r in df.iterrows():
        w, v = r["collocate"], float(r[value])
        width = max(4, round(v / vmax * 100))
        items.append(
            f'<li><span class="w">{html.escape(r["collocate"])}</span>'
            f'<span class="bar"><i style="width:{width}%"></i></span>'
            f'<span class="n">{fmt.format(v)}</span></li>')
    return f'<div class="sbs-col"><h4>{html.escape(label)}</h4><ol>{"".join(items)}</ol></div>'

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
        ("CSV 結果表", "12 份"),
    ]
    return '<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{html.escape(k)}</div><div class="v">{html.escape(v)}</div></div>'
        for k, v in cards) + "</div>"

def render_curves() -> str:
    path = os.path.join(OUT_DIR, "character_space_by_chapter.csv")
    if not os.path.exists(path):
        return ""
    cs = pd.read_csv(path)
    top5 = cs.sort_values("黛玉_share", ascending=False).head(5)
    chips = "".join(f'<span class="chip">第 {int(r.chapter)} 回 · {r["黛玉_share"]:.2f}%</span>'
                    for _, r in top5.iterrows())
    avg_front = cs[cs.chapter <= 80]["黛玉_share"].mean()
    avg_back = cs[cs.chapter > 80]["黛玉_share"].mean()
    return (f'<h2><span class="sec-no">二</span>人物空間曲線：各回的敘事注意力份額</h2>'
            f'<p class="meta">Woloch 的「人物空間」最直接的量化：每一回中，角色詞出現次數佔全章詞數的比例'
            f'（3 回滑動平均平滑）。這是「被暗示的人」與「話語分配的篇幅」之間的張力曲線。'
            f'完整數據：<a href="character_space_by_chapter.csv" download>⤓ character_space_by_chapter.csv</a></p>'
            f'<img class="wide" src="plot_char_space_curves.png" alt="人物空間曲線">'
            f'<p class="meta">黛玉空間份額最高的五回：{chips}　'
            f'前 80 回平均 <strong>{avg_front:.2f}%</strong>，後 40 回平均 <strong>{avg_back:.2f}%</strong>。</p>')

def render_network() -> str:
    p = os.path.join(OUT_DIR, "plot_daiyu_network.png")
    if not os.path.exists(p):
        return ""
    return (f'<h2><span class="sec-no">三</span>搭配詞網絡</h2>'
            f'<p class="meta">以 obs_local 為邊權、全書詞頻為節點大小的力導向圖——'
            f'黛玉人物空間的關係拓撲：人物名（宝玉/宝钗/紫鹃…）構成核心，'
            f'套語與場景詞（只见/一面/起来）構成外圍。</p>'
            f'<img class="wide" src="plot_daiyu_network.png" alt="黛玉搭配詞網絡">')

def render_measures(tables: dict) -> str:
    t = tables.get("collocates_daiyu_window_h5_measures")
    if not t:
        return ""
    df = t["df"]
    sbs = (rank_list(df, "log_dice", 10, "top 10 · logDice（結合強度）", "{:.2f}")
           + rank_list(df, "t_score", 10, "top 10 · t-score（高頻偏好）", "{:.2f}")
           + rank_list(df.assign(obs=df["obs_local"]), "obs", 10, "top 10 · obs_local（原始共現）", "{:,.0f}"))
    return (f'<h2><span class="sec-no">五</span>測度比較：同一張列聯表，三種排序</h2>'
            f'<p class="meta">p 值只回答「顯著嗎」；排序還需要效度測度。logDice 獎勵「專屬性」'
            f'（少見但緊密），t-score 獎勵高頻共現——兩種視角下黛玉空間的頭部詞不同。'
            f'完整表：<a href="{t["csv"]}" download>⤓ {t["csv"]}</a></p>'
            f'<div class="sbs">{sbs}</div>')

def render_names_check(tables: dict) -> str:
    t = tables.get("collocates_daiyu_pooled_h5")
    plain = tables.get("collocates_daiyu_window_h5")
    if not (t and plain):
        return ""
    note_path = os.path.join(OUT_DIR, "pooled_overlap_note.txt")
    note = ""
    if os.path.exists(note_path):
        with open(note_path, encoding="utf-8") as f:
            note = f.read()
    pre = html.escape(note.split("\n")[1]) if "\n" in note else ""
    only_pool = html.escape(note.split("\n")[2].replace("only in pooled top-50: ", "")) if note else ""
    return (f'<h2><span class="sec-no">六</span>名稱變體檢核：黛玉 vs 黛玉＋林黛玉</h2>'
            f'<p class="meta">全名「林黛玉」在分詞詞表中出現 247 次，'
            f'與「黛玉」合併為同一目標（pooled）後，top-50 有 {pre[13:] if pre.startswith("top-50 overlap") else pre}。'
            f'併集獨有的詞：{only_pool}——全名多出現在敘述框架句（初見、怡紅院、母親），'
            f'單名多出現在直接場景。名稱的選擇本身就是人物空間的話語標記。'
            f'完整表：<a href="{t["csv"]}" download>⤓ {t["csv"]}</a></p>')

def render_glossary() -> str:
    cards = "".join(
        f'<div class="gloss"><strong>{html.escape(w)}</strong><p>{html.escape(t)}</p></div>'
        for w, t in GLOSSARY.items())
    return (f'<h2><span class="sec-no">十二</span>重點搭配詞注釋</h2>'
            f'<p class="meta">把統計結果拉回文本知識——表中被 hover 提示的詞，注釋如下。</p>'
            f'<div class="glossary">{cards}</div>')

def render_kwic(path: str, limit: int = 24) -> str:
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln and not ln.startswith("KWIC")][1:]
    sample = lines[:: max(1, len(lines) // limit)][:limit]
    lis = "".join(f"<li>{html.escape(ln).replace('黛玉', '<mark>黛玉</mark>')}</li>"
                  for ln in sample)
    return f'<ol class="kwic">{lis}</ol>'

def main() -> None:
    tables = load_tables()
    if not tables:
        raise SystemExit(f"no CSV files matching {CSV_PATTERN} — run collocates.py first")

    # ---------- 一 quick comparison ----------
    base_ids = ["collocates_daiyu_window_h5", "collocates_daiyu_window_h10", "collocates_daiyu_sentence"]
    quick = ""
    if all(i in tables for i in base_ids):
        h5 = tables["collocates_daiyu_window_h5"]["df"]
        h10 = tables["collocates_daiyu_window_h10"]["df"]
        stc = tables["collocates_daiyu_sentence"]["df"]
        sbs = (rank_list(h5, "obs_local", 15, "視窗 horizon=5", "{:,.0f}")
               + rank_list(h10, "obs_local", 15, "視窗 horizon=10", "{:,.0f}")
               + rank_list(stc, "obs_local", 15, "句子法", "{:,.0f}"))
        quick = (f'<h2><span class="sec-no">一</span>速覽：三種「鄰近」定義下的黛玉（top 15）</h2>'
                 f'<p class="meta">橫條長度＝obs_local 相對大小。三欄的差異就是操作化的「人物空間邊界」。</p>'
                 f'<div class="sbs">{sbs}</div>')

    # ---------- 四 grouped tables ----------
    sec_no = {"basic": "四", "chars": "七", "time": "八", "names": "六", "fdr": "九"}
    sections = []
    for key, gtitle, ids in GROUPS:
        avail = [i for i in ids if i in tables]
        if not avail:
            continue
        parts = [f'<h2 id="g-{key}"><span class="sec-no">{sec_no[key]}</span>{html.escape(gtitle)}</h2>']
        for t_id in avail:
            t = tables[t_id]
            n = len(t["df"])
            max_p = t["df"]["p_value"].max()
            parts.append(
                f'<details open class="tbl"><summary>{html.escape(t["label"])}'
                f'<span class="badge">{n:,} 搭配詞 · max p = {max_p:.3g}</span></summary>'
                f'<p class="meta"><a href="{t["csv"]}" download>⤓ 下載此表 CSV</a></p>'
                + render_table(t, "tbl-" + t_id) + "</details>")
        sections.append("".join(parts))
    section_html = "".join(sections)

    # ---------- 十 plots ----------
    skip = {"plot_char_space_curves.png", "plot_daiyu_network.png"}
    plot_caps = {
        "plot_daiyu_h5_top15": "黛玉 top 15（視窗 h5）",
        "plot_daiyu_h10_top15": "黛玉 top 15（視窗 h10）",
        "plot_daiyu_sentence_top15": "黛玉 top 15（句子法）",
        "plot_daiyu_ratio_top15": "top 15（obs/exp 比，obs≥10）——最排他的搭配詞",
        "plot_three_chars_overlap": "三角色 top-50 重疊矩陣",
        "plot_daiyu_front_back": "前 80 回 vs 後 40 回 top 15 對照",
    }
    plots = [p for p in sorted(glob.glob(os.path.join(OUT_DIR, "plot_*.png")))
             if os.path.basename(p) not in skip]
    gallery = ""
    if plots:
        figs = "".join(
            f'<figure><img src="{os.path.basename(p)}" loading="lazy" alt="{os.path.basename(p)}">'
            f'<figcaption>{html.escape(plot_caps.get(os.path.splitext(os.path.basename(p))[0], os.path.basename(p)))}</figcaption></figure>'
            for p in plots)
        gallery = f'<h2><span class="sec-no">十</span>圖表總覽</h2><div class="gallery">{figs}</div>'

    # ---------- 十一 kwic ----------
    kwic_html = ""
    kwic_path = os.path.join(OUT_DIR, "kwic_daiyu.txt")
    if os.path.exists(kwic_path):
        kwic_html = (f'<h2><span class="sec-no">十一</span>KWIC 脈絡例句（抽樣）</h2>'
                     f'<p class="meta">自原文抽樣黛玉出現處（±30 字）；完整清單見 <code>output/kwic_daiyu.txt</code>。</p>'
                     + render_kwic(kwic_path))

    nav = [("quick", "速覽"), ("curves", "曲線"), ("network", "網絡"),
           ("g-basic", "基礎表"), ("g-names", "變體"), ("g-chars", "角色對照"),
           ("g-time", "前後期"), ("g-fdr", "FDR"), ("plots", "圖表"),
           ("kwic", "KWIC"), ("glossary", "注釋"), ("methods", "方法")]
    nav_html = '<nav class="topnav">' + "".join(
        f'<a href="#{i}">{t}</a>' for i, t in nav) + "</nav>"

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>瀟湘館裡的詞與人——黛玉的搭配詞與人物空間</title>
<style>
  :root {{
    --paper: #f6efe0; --ink: #3a2e2a; --faint: #7a6a5c;
    --jiang: #8b2f2f; --dai: #3f5c54; --line: #d9c9a8; --gold: #b08d4f;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
    background: var(--paper); color: var(--ink); margin: 0;
    background-image: repeating-linear-gradient(0deg, transparent 0 27px, rgba(176,141,79,.06) 27px 28px);
  }}
  .wrap {{ max-width: 1150px; margin: 0 auto; padding: 0 1.2rem 4rem; }}
  nav.topnav {{
    position: sticky; top: 0; z-index: 50; backdrop-filter: blur(6px);
    background: rgba(246,239,224,.92); border-bottom: 1px solid var(--line);
    padding: .45rem 0; text-align: center;
  }}
  nav.topnav a {{
    color: var(--dai); text-decoration: none; font-size: .88rem; margin: 0 .45rem;
    border-bottom: 2px solid transparent; padding: .1rem .15rem;
  }}
  nav.topnav a:hover {{ color: var(--jiang); border-color: var(--jiang); }}
  header.banner {{ text-align: center; padding: 2.4rem 1rem 1.6rem;
                  border-bottom: 3px double var(--line); margin-bottom: 1.4rem; }}
  header.banner h1 {{
    font-family: "Kaiti TC", "DFKai-SB", KaiTi, "STKaiti", serif;
    font-size: 2.1rem; letter-spacing: .14em; margin: .2rem 0; color: var(--jiang);
  }}
  header.banner .sub {{ color: var(--faint); letter-spacing: .08em; font-size: .95rem; }}
  header.banner .seal {{
    display: inline-block; border: 2px solid var(--jiang); color: var(--jiang);
    font-family: "Kaiti TC", "DFKai-SB", KaiTi, serif; padding: .1rem .5rem;
    border-radius: 4px; font-size: .9rem; letter-spacing: .3em; margin-top: .6rem;
  }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .8rem; margin: 1.3rem 0; }}
  .card {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px;
          padding: .8rem .9rem; text-align: center; box-shadow: 0 1px 3px rgba(90,60,30,.08); }}
  .card .k {{ font-size: .8rem; color: var(--faint); letter-spacing: .06em; }}
  .card .v {{ font-size: 1.22rem; font-weight: 700; color: var(--dai); margin-top: .2rem; }}
  h2 {{ font-family: "Kaiti TC", "DFKai-SB", KaiTi, serif; color: var(--jiang);
       border-bottom: 1px solid var(--line); padding-bottom: .35rem; margin-top: 2.6rem;
       font-size: 1.32rem; letter-spacing: .05em; }}
  .sec-no {{ display: inline-block; background: var(--jiang); color: #fff; font-size: .8rem;
           width: 1.6em; height: 1.6em; line-height: 1.6em; text-align: center;
           border-radius: 50%; margin-right: .5rem; vertical-align: 2px; }}
  .meta {{ color: var(--faint); font-size: .88rem; line-height: 1.65; }}
  .meta a {{ color: var(--dai); }}
  code {{ background: #efe6d2; padding: 0 .3em; border-radius: 4px; font-size: .85em; }}
  img.wide {{ max-width: 100%; display: block; margin: .8rem auto; border: 1px solid var(--line);
            border-radius: 10px; background: #fffdf6; padding: .5rem; }}
  .chip {{ display: inline-block; background: #efe4c8; color: var(--jiang); border: 1px solid var(--line);
          border-radius: 99px; padding: .1rem .6rem; font-size: .82rem; margin: .15rem .2rem .15rem 0; }}
  details.tbl {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px;
               margin: 1rem 0; padding: .6rem .9rem; box-shadow: 0 1px 3px rgba(90,60,30,.08); }}
  details.tbl summary {{ cursor: pointer; font-weight: 700; color: var(--dai); font-size: 1.02rem; }}
  .badge {{ font-weight: 400; font-size: .78rem; color: var(--faint); margin-left: .6rem;
          border: 1px solid var(--line); padding: .05rem .5rem; border-radius: 99px; }}
  input.tbl-search {{
    margin: .6rem 0 .2rem; padding: .35rem .7rem; border: 1px solid var(--line);
    border-radius: 99px; background: #fffdf6; color: var(--ink); width: 240px;
    font-size: .88rem; outline: none;
  }}
  input.tbl-search:focus {{ border-color: var(--dai); }}
  .table-wrap {{ overflow-x: auto; max-height: 460px; margin-top: .4rem; border: 1px solid var(--line); }}
  table {{ border-collapse: collapse; font-size: .9rem; width: 100%; }}
  th, td {{ border: 1px solid #e3d7bd; padding: .3rem .55rem; text-align: right; white-space: nowrap; }}
  th:first-child, td:first-child {{ text-align: left; }}
  thead th {{ background: var(--dai); color: #f6efe0; position: sticky; top: 0; font-weight: 600; }}
  tbody tr:nth-child(even) {{ background: #f7f2e4; }}
  tbody tr:hover {{ background: #efe4c8; }}
  .sbs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
  .sbs-col {{ background: #fffdf6; border: 1px solid var(--line); border-radius: 10px; padding: .7rem 1rem; }}
  .sbs-col h4 {{ margin: .1rem 0 .6rem; color: var(--dai); font-size: .98rem; }}
  .sbs-col ol {{ list-style: none; margin: 0; padding: 0; counter-reset: rk; }}
  .sbs-col li {{ display: grid; grid-template-columns: 3.4em 1fr 3.9em; align-items: center;
               gap: .5rem; padding: .12rem 0; counter-increment: rk; font-size: .95rem; }}
  .sbs-col li::before {{ content: counter(rk); color: var(--gold); font-variant-numeric: tabular-nums;
                       text-align: right; }}
  .sbs-col .w {{ font-weight: 700; }}
  .sbs-col .bar {{ background: #ece2c8; border-radius: 3px; height: .8em; overflow: hidden; }}
  .sbs-col .bar i {{ display: block; height: 100%; background: linear-gradient(90deg, var(--dai), var(--jiang)); }}
  .sbs-col .n {{ color: var(--faint); font-size: .82rem; text-align: right; font-variant-numeric: tabular-nums; }}
  ol.kwic {{ list-style: none; padding: 0; columns: 2; column-gap: 2rem; font-size: .92rem; }}
  ol.kwic li {{ margin: 0 0 .45rem; padding: .35rem .6rem; background: #fffdf6;
              border: 1px solid var(--line); border-radius: 6px; break-inside: avoid; }}
  ol.kwic mark {{ background: #f3d9c8; color: var(--jiang); font-weight: 700; padding: 0 .15em; border-radius: 3px; }}
  .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1rem; }}
  figure {{ margin: 0; border: 1px solid var(--line); padding: .6rem; background: #fffdf6;
          border-radius: 10px; }}
  figure img {{ max-width: 100%; display: block; margin: 0 auto; }}
  figcaption {{ font-size: .82rem; color: var(--faint); margin-top: .5rem; text-align: center; }}
  .glossary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: .8rem; }}
  .gloss {{ background: #fffdf6; border: 1px solid var(--line); border-left: 4px solid var(--jiang);
          border-radius: 8px; padding: .7rem .9rem; font-size: .9rem; }}
  .gloss strong {{ color: var(--dai); font-size: 1rem; }}
  .gloss p {{ margin: .3rem 0 0; color: #57493f; line-height: 1.55; }}
  footer.methods {{ margin-top: 3rem; border-top: 3px double var(--line); padding-top: 1.2rem;
                  font-size: .88rem; color: var(--faint); }}
  footer.methods dt {{ font-weight: 700; color: var(--dai); }}
  footer.methods dd {{ margin: 0 0 .5rem 1.2em; line-height: 1.6; }}
</style>
</head>
<body>
{nav_html}
<div class="wrap">
<header class="banner">
  <div class="sub">搭配詞分析 × Woloch 人物空間</div>
  <h1>瀟湘館裡的詞與人</h1>
  <div class="sub">《紅樓夢》一百二十回・目標詞「黛玉」</div>
  <div class="seal">石頭記</div>
</header>
{render_stats()}
{quick}
{render_curves()}
{render_network()}
{section_html}
{render_measures(tables)}
{render_names_check(tables)}
{gallery}
{kwic_html}
{render_glossary()}
<footer class="methods" id="methods">
  <h2><span class="sec-no">+</span>方法註記</h2>
  <dl>
    <dt>流程</dt><dd>opencc 繁→簡（本語料已為簡體，轉換為 no-op）→ 中文句末標點分句（。！？）→ jieba 分詞 → 移除標點 → 保留 ≥5 詞的句子（segment.py）。</dd>
    <dt>停用詞</dt><dd>qhchina.load_stopwords()（zh_sim，806 詞），經 filters 傳入 find_collocates。</dd>
    <dt>統計</dt><dd>每個搭配詞對目標詞建立 2×2 列聯表（Evert 2008：O11=obs_local、E11=exp_local、R1=目標詞上下文大小、C1=obs_global、N=總詞數），以 Fisher 精確檢定求 p 值；alternative="greater"（單尾——只檢定「共現高於隨機預期」）。</dd>
    <dt>filters</dt><dd>min_word_length=2（聚焦雙字詞以上）、max_p=0.05（表內每列 p &lt; 0.05）、stopwords；FDR 版另以 Benjamini–Hochberg 校正。</dd>
    <dt>設定</dt><dd>window horizon=5 / 10（目標詞左右各 5／10 詞）與 sentence（同一句為共現單位）；另含 pooled（黛玉＋林黛玉併集）與多測度（logDice、t-score、G²）版本。</dd>
    <dt>欄位</dt><dd>obs_local＝實際共現；exp_local＝隨機期望；ratio_local＝obs/exp；obs_global＝搭配詞全書頻率；p_value＝Fisher 精確檢定。</dd>
    <dt>腳本</dt><dd>segment.py（分詞）→ collocates.py（基礎三設定）→ analysis_extended.py（角色對照、前後期、FDR、KWIC、基礎圖表）→ analysis_premium.py（曲線、網絡、測度、名稱變體）→ make_report.py（本頁）。</dd>
  </dl>
</footer>
</div>
<script>
document.querySelectorAll('.tbl-search').forEach(function(inp){{
  inp.addEventListener('input', function(){{
    var q = inp.value.trim();
    document.querySelectorAll('#' + inp.dataset.tbl + ' tbody tr').forEach(function(tr){{
      tr.style.display = tr.textContent.indexOf(q) !== -1 ? '' : 'none';
    }});
  }});
}});
</script>
</body>
</html>"""
    out = os.path.join(OUT_DIR, "results.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"written {out}: {len(tables)} tables, sections: 一二三 + {len(sections)} groups")

if __name__ == "__main__":
    main()