"""Segment the Hong Lou Meng corpus into simplified-Chinese sentences.

Steps (week-4 lecture, prompt 1):
1. load data/hongloumeng.txt (UTF-8)
2. convert the whole text to simplified Chinese with opencc
   (jieba works better with simplified characters)
3. split the text into sentences using Chinese sentence-ending punctuation (。！？)
4. tokenize each sentence into words with jieba, removing punctuation marks
5. keep only sentences with at least 5 words
6. save the result as data/sentences.txt, one sentence per line, with the words
   in each sentence separated by a single space, so it can be reused without
   re-segmenting every time
"""
import re
from collections import Counter

import opencc
import jieba

DATA = "data/hongloumeng.txt"
OUT = "data/sentences.txt"

# 1. load
with open(DATA, encoding="utf-8") as f:
    text = f.read()
print(f"loaded {DATA}: {len(text):,} chars")

# 2. traditional -> simplified (no-op if the corpus is already simplified)
cc = opencc.OpenCC("t2s")
text = cc.convert(text)
print("converted to simplified Chinese (t2s)")

# 3. sentences
raw_chunks = re.split(r"[。！？]+", text)
print(f"split into {len(raw_chunks):,} raw sentence chunks")

# a word must consist of CJK characters, digits, or latin letters
# (this removes all punctuation marks, including Chinese ones)
word_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf0-9A-Za-z]+")

# 4-5. tokenize each sentence, remove punctuation, keep sentences with >= 5 words
kept = []
total_words = 0
for chunk in raw_chunks:
    words = [w for w in jieba.lcut(chunk) if word_re.fullmatch(w)]
    if len(words) >= 5:
        kept.append(words)
        total_words += len(words)

print(f"kept {len(kept):,} sentences with at least 5 words")
print(f"total words kept: {total_words:,}")

# 6. save, one sentence per line, single space between words
with open(OUT, "w", encoding="utf-8") as f:
    for words in kept:
        f.write(" ".join(words) + "\n")
print("saved:", OUT)

# --- stats, useful for choosing the target word ---
counter = Counter(w for words in kept for w in words)
print("vocab size:", len(counter))
for w in ["林黛玉", "黛玉", "贾宝玉", "宝玉", "林", "黛", "玉"]:
    print(f"token count {w!r}: {counter[w]:,}")
print("top 30 tokens:")
for w, n in counter.most_common(30):
    print(f"  {w}: {n:,}")