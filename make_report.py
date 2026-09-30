"""Build a single HTML page (output/results.html) that combines all collocate
CSV files in output/ into one page, with a dropdown to switch between tables
so they can be compared without opening each CSV separately.

Week-4 lecture, prompt 3.
"""
import glob
import html
import os
import re

import pandas as pd

OUT_DIR = "output"
CSV_PATTERN = os.path.join(OUT_DIR, "collocates_*.csv")

PRETTY_NAMES = {
    "window_h5": "window, horizon=5",
    "window_h10": "window, horizon=10",
    "sentence": "sentence (whole-sentence co-occurrence)",
    "front80_window_h5": "window h5, chapters 1-80",
    "back40_window_h5": "window h5, chapters 81-120",
}

def prettify_label(stem: str) -> str:
    # collocates_daiyu_window_h5 -> 黛玉 · window, horizon=5
    # collocates_daiyu_window_h5_fdr -> 黛玉 · window, horizon=5 (FDR-adjusted)
    m = re.match(r"collocates_(?P<target>.+?)_(?P<run>window_h\d+|sentence|front80_window_h5|back40_window_h5)(?P<extra>_fdr)?$", stem)
    if not m:
        return stem
    target, run = m.group("target"), m.group("run")
    desc = PRETTY_NAMES.get(run, run)
    if m.group("extra"):
        desc += " · FDR corrected"
    return f"{target} · {desc}"

NUM_COLS = {"exp_local", "ratio_local", "obs_global", "p_value",
            "log_likelihood", "log_dice", "t_score", "mi"}

def load_tables() -> list[dict]:
    tables = []
    for path in sorted(glob.glob(CSV_PATTERN)):
        df = pd.read_csv(path)
        stem = os.path.splitext(os.path.basename(path))[0]
        tables.append({"id": stem, "label": prettify_label(stem), "df": df})
    if not tables:
        raise SystemExit(f"no CSV files matching {CSV_PATTERN} — run collocates.py first")
    return tables

def render_table(tab: dict) -> str:
    df = tab["df"]
    # move adjusted_p_value next to p_value when present
    if "adjusted_p_value" in df.columns:
        cols = [c for c in df.columns if c != "adjusted_p_value"]
        cols.insert(cols.index("p_value") + 1, "adjusted_p_value")
        df = df[cols]
        tab = {**tab, "df": df}
    num_cols = set(df.columns) & NUM_COLS
    rows = []
    for _, r in df.iterrows():
        cells = []
        for col in df.columns:
            v = r[col]
            if col in num_cols and pd.notna(v):
                if col in ("p_value", "adjusted_p_value"):
                    # keep significant small p-values readable
                    text = f"{v:.3g}"
                elif col in ("exp_local", "ratio_local"):
                    text = f"{v:.3g}"
                else:
                    text = f"{v:,.0f}" if float(v).is_integer() else f"{v:.3g}"
            elif col == "collocate":
                text = f'<strong>{html.escape(str(v))}</strong>'
            else:
                text = html.escape(str(v))
            cells.append(f"<td>{text}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{html.escape(c)}</th>" for c in tab["df"].columns)
    n = len(tab["df"])
    return (f'<div class="table-wrap" id="{tab["id"]}" hidden>'
            f'<p class="meta">{n} collocates (p &lt; 0.05), sorted by obs_local (high to low)</p>'
            f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

def main() -> None:
    tables = load_tables()

    options = "".join(
        f'<option value="{t["id"]}"{" selected" if i == 0 else ""}>{html.escape(t["label"])}</option>'
        for i, t in enumerate(tables)
    )
    selects = "".join(render_table(t) for t in tables)

    plots = sorted(glob.glob(os.path.join(OUT_DIR, "plot_*.png")))
    gallery = ""
    if plots:
        figs = "".join(
            f'<figure><img src="{os.path.basename(p)}" alt="{os.path.basename(p)}">'
            f'<figcaption>{html.escape(os.path.basename(p).replace("plot_", "").replace(".png", ""))}</figcaption></figure>'
            for p in plots)
        gallery = f"<h2>Plots</h2><div class='gallery'>{figs}</div>"

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>黛玉 collocates — comparison</title>
<style>
  body {{ font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
         margin: 2rem auto; max-width: 1100px; padding: 0 1rem; color: #222; }}
  h1 {{ font-size: 1.4rem; }}
  .meta {{ color: #666; font-size: .9rem; }}
  select {{ font-size: 1rem; padding: .4rem .6rem; margin: 1rem 0; }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; font-size: .92rem; min-width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: .35rem .6rem; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  thead th {{ background: #f3ede4; position: sticky; top: 0; }}
  tbody tr:nth-child(even) {{ background: #faf7f2; }}
  h2 {{ margin-top: 2rem; font-size: 1.15rem; }}
  .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
             gap: 1rem; }}
  figure {{ margin: 0; border: 1px solid #ddd; padding: .5rem; background: #fff; }}
  figure img {{ max-width: 100%; display: block; margin: 0 auto; }}
  figcaption {{ font-size: .8rem; color: #666; margin-top: .4rem; text-align: center;
               word-break: break-all; }}
</style>
</head>
<body>
<h1>《紅樓夢》搭配詞分析：黛玉（目标词：黛玉）</h1>
<p class="meta">
  corpus: 《红楼梦》(曹雪芹, 120-chapter edition, ~860k chars) ·
  target: <strong>黛玉</strong> · filters: min_word_length=2, max_p=0.05,
  stopwords removed · sorted by obs_local ↓ · p-value: Fisher's exact test
  (alternative="greater")
</p>
<label for="pick">選擇設定：</label>
<select id="pick" onchange="show(this.value)">{options}</select>
{selects}
{gallery}
<script>
function show(id) {{
  document.querySelectorAll(".table-wrap").forEach(d => d.hidden = d.id !== id);
}}
show(document.getElementById("pick").value);
</script>
</body>
</html>"""
    out = os.path.join(OUT_DIR, "results.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"written {out} with {len(tables)} tables:",
          ", ".join(t["label"] for t in tables))

if __name__ == "__main__":
    main()