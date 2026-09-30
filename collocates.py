"""Find collocates for the target character with qhchina's find_collocates.

Week-4 lecture, prompt 2:
- target word: 黛玉 (simplified; the corpus was converted with opencc)
- find_collocates from qhchina.analytics.collocations
- remove stopwords via load_stopwords() from qhchina (passed in `filters`)
- keep only collocates with at least 2 characters (min_word_length=2)
- keep only significant collocates (max_p=0.05)
- three runs: window/horizon=5, window/horizon=10, sentence
- each result sorted by obs_local (high to low) and saved to its own CSV
- top 20 rows of each printed to the terminal
"""
import os

import pandas as pd
from qhchina import load_stopwords
from qhchina.analytics.collocations import find_collocates

TARGET = "黛玉"
SENTENCES_FILE = "data/sentences.txt"
OUT_DIR = "output"

stopwords = load_stopwords()  # default: zh_sim (simplified, modern Chinese)
print(f"loaded {len(stopwords)} stopwords")

# load the pre-segmented sentences (list of token lists; restartable, as required)
sentences = []
with open(SENTENCES_FILE, encoding="utf-8") as f:
    for line in f:
        tokens = line.split()
        if tokens:
            sentences.append(tokens)
print(f"loaded {len(sentences):,} sentences")

filters = {
    "stopwords": stopwords,
    "min_word_length": 2,   # focus on disyllabic words and longer
    "max_p": 0.05,          # only statistically significant collocates
}

runs = [
    ("window_h5",       dict(method="window", horizon=5)),
    ("window_h10",      dict(method="window", horizon=10)),
    ("sentence",        dict(method="sentence")),   # no horizon for sentence method
]

os.makedirs(OUT_DIR, exist_ok=True)

for name, kwargs in runs:
    print(f"\n=== run: {name} (target={TARGET}, {kwargs}) ===")
    df = find_collocates(
        sentences=sentences,
        target_words=TARGET,
        filters=filters,
        sort_by="obs_local",
        ascending=False,
        return_type="dataframe",
        **kwargs,
    )
    path = os.path.join(OUT_DIR, f"collocates_daiyu_{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"saved {len(df)} collocates -> {path}")
    print(f"top 20 (of {len(df)}):")
    cols = ["collocate", "obs_local", "exp_local", "ratio_local", "obs_global", "p_value"]
    with pd.option_context("display.max_rows", 25, "display.width", 120,
                           "display.float_format", lambda v: f"{v:.4g}"):
        print(df[cols].head(20).to_string(index=False))
