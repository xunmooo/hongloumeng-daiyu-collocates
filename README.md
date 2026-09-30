# 搭配詞與「人物空間」：《紅樓夢》中的黛玉

以 qhchina 的 `find_collocates` 考察《紅樓夢》中「黛玉」一詞的搭配詞側寫，
作為 Woloch「人物空間」（character-space）概念的統計操作化嘗試。

## 語料

- **書名**：《紅樓夢》（又名《石頭記》），一百二十回本
- **作者**：曹雪芹（前八十回）；後四十回傳為高鶚、程偉元整理
- **來源**：<https://github.com/tennessine/corpus>（公版全文，UTF-8 純文字）
- **規模**：約 86 萬字；分詞後保留 12,884 個 ≥5 詞的句子，共約 44.9 萬詞
- **目標詞**：`黛玉`（分詞後出現 548 次）

## 重現步骤

```bash
pip install -r requirements.txt

python segment.py               # opencc 繁→簡 → 分句（。！？）→ jieba 分詞 → data/sentences.txt
python collocates.py            # find_collocates：window h5 / window h10 / sentence → output/*.csv
python analysis_extended.py     # 擴充分析（見下）→ output/*.csv / *.png / kwic_daiyu.txt
python make_report.py           # 整合所有表與圖 → output/results.html
```

- `report.md` / `report.pdf`：報告（同一篇的兩種格式）

## 分析設計

**基礎（第 4 週講義）**：黛玉 × 3 種設定（window h5、window h10、sentence），
Fisher 精確檢定（`alternative="greater"`），filters：`min_word_length=2`、`max_p=0.05`、停用詞。

**擴充**（`analysis_extended.py`）：

1. **多角色對照**：宝玉、宝钗 以同樣設定（window h5）各跑一次，與黛玉比較
   top-50 搭配詞的重疊與差異——檢視「人物空間」的分配差異
2. **敘事時間切分**：前 80 回 vs 後 40 回分別分析黛玉（人物空間隨敘事推進的變化）
3. **FDR 校正**（Benjamini-Hochberg）：三種基礎設定各附一版
   `adjusted_p_value`（全部通過 0.05）
4. **KWIC 例句**：`output/kwic_daiyu.txt`，黛玉的抽樣脈絡（±30 字）
5. **圖表**：各設定 top15 長條圖、obs/exp 比圖、三角色重疊矩陣、前後期對照表
   （`output/plot_*.png`）

## 方法

- 分句：以中文句末標點（。！？）切分；分詞：jieba；停用詞：`qhchina.load_stopwords()`
- 正規化：opencc（`t2s`）——本語料檔已為簡體，轉換為 no-op，但流程保留
- 統計：`find_collocates`（Fisher 精確檢定，`alternative="greater"`），
  filters：`min_word_length=2`、`max_p=0.05`、`stopwords`
- 三種設定比較：`method="window", horizon=5`、`horizon=10`、`method="sentence"`
- 每次結果各存一個 CSV（`output/collocates_*.csv`），
  整合比較頁（含全部表與圖）：`output/results.html`
