"""Robust chapter splitting for data/hongloumeng.txt.

Handles the quirks of this particular corpus file:
- chapter numbers without 百 (第一零零回 = ch.100, 第一一零回 = ch.110)
- TOC-style heading lines (tiny chunk) whose body starts with a
  cross-reference like 「第四回中既将薛家母子……」 or 「第一回也．作者自云」
  -> the reference chunk belongs to the tiny heading's chapter
- duplicate headings (TOC line + real body) -> chunks are concatenated
"""
import re

import opencc

HEAD = re.compile(r"第([零一二三四五六七八九十百廿\d]+)回")
# characters that, right after 「回」, mark a cross-reference rather than a heading
PARTICLES = set("中也的已里内上时后前间之而着过")


def _cn2num(t: str) -> int:
    digits = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
    if t.isdigit():
        return int(t)
    if "百" in t or "十" in t or "廿" in t:
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
    # no magnitude word: positional digits (一零零=100, 一零一=101, 一一零=110)
    if len(t) == 3:
        return digits.get(t[0], 0) * 100 + digits.get(t[1], 0) * 10 + digits.get(t[2], 0)
    if len(t) == 2:
        return digits.get(t[0], 0) * 10 + digits.get(t[1], 0)
    return digits.get(t, -1)


def load_text(path: str = "data/hongloumeng.txt") -> str:
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return opencc.OpenCC("t2s").convert(raw)


def split_chapters(raw: str) -> dict[int, str]:
    ms = list(HEAD.finditer(raw))
    items = []
    for m in ms:
        num = _cn2num(m.group(1))
        after = raw[m.end():m.end() + 1]
        items.append({"start": m.start(), "end": m.end(), "num": num,
                      "is_ref": bool(after) and after in PARTICLES})

    chunks: dict[int, list[str]] = {}
    pending: int | None = None
    for i, it in enumerate(items):
        end = items[i + 1]["start"] if i + 1 < len(items) else len(raw)
        body = raw[it["start"]:end]
        if it["is_ref"] and pending is not None:
            chunks.setdefault(pending, []).append(body)
            pending = None
        else:
            chunks.setdefault(it["num"], []).append(body)
            pending = it["num"] if (end - it["start"]) < 300 else None
    return {k: "".join(v) for k, v in sorted(chunks.items()) if k > 0}


def load_chapters(path: str = "data/hongloumeng.txt") -> dict[int, str]:
    return split_chapters(load_text(path))


if __name__ == "__main__":
    chs = load_chapters()
    print("chapters parsed:", len(chs))
    print("sizes (chars): min", min(len(v) for v in chs.values()),
          "max", max(len(v) for v in chs.values()))
    tiny = [(k, len(v)) for k, v in chs.items() if len(v) < 1000]
    print("suspiciously small chapters:", tiny)
    print("total chars:", sum(len(v) for v in chs.values()))
    front = sum(len(v) for k, v in chs.items() if k <= 80)
    back = sum(len(v) for k, v in chs.items() if k > 80)
    print(f"front(1-80): {front:,} chars | back(81-120): {back:,} chars")