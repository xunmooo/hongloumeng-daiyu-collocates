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

python segment.py       # opencc 繁→簡 → 分句（。！？）→ jieba 分詞 → data/sentences.txt
python collocates.py    # find_collocates：window h5 / window h10 / sentence → output/*.csv
python make_report.py   # 整合三張表 → output/results.html
```

- `report.md` / `report.pdf`：報告（同一篇的兩種格式）

## 方法

- 分句：以中文句末標點（。！？）切分；分詞：jieba；停用詞：`qhchina.load_stopwords()`
- 正規化：opencc（`t2s`）——本語料檔已為簡體，轉換為 no-op，但流程保留
- 統計：`find_collocates`（Fisher 精確檢定，`alternative="greater"`），
  filters：`min_word_length=2`、`max_p=0.05`、`stopwords`
- 三種設定比較：`method="window", horizon=5`、`horizon=10`、`method="sentence"`
- 每次結果各存一個 CSV（`output/collocates_daiyu_*.csv`），
  整合比較頁：`output/results.html`
