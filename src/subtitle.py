"""SRT 字幕生成：把带时间戳的句子转换为 SubRip 文本。

DashScope 文件转写在 ``transcripts[0].sentences`` 中给出一句话及其词的
起止时间（毫秒）。本模块只做纯数据转换，不依赖任何外部服务，便于离线测试。
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence

# 单条字幕的上限：超过后按词边界拆开，避免整段话挤在一条里。
MAX_CUE_SECONDS = 20.0
MAX_CUE_CHARS = 42

# 句子以这些符号结尾时，优先在此处断句。
_BREAK_PUNCTUATION = set("，,。.；;！!？?、：:…")


def _to_milliseconds(value) -> int:
    """把毫秒时间戳规范为非负整数；非法值视为 0。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0
    if number != number or number in (float("inf"), float("-inf")):  # NaN / inf
        return 0
    return max(0, int(round(number)))


def format_timestamp(milliseconds: int) -> str:
    """格式化为 SRT 时间戳 ``HH:MM:SS,mmm``。"""
    milliseconds = _to_milliseconds(milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _clean_text(text) -> str:
    if not isinstance(text, str):
        return ""
    # SRT 以空行分隔字幕条目，块内换行会破坏格式。
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def _segment_by_words(sentence: dict, max_chars: int, max_milliseconds: int) -> list[tuple[int, int, str]]:
    """按词边界把一句话拆成多条，保证每条不超长、不超时。"""
    words = sentence.get("words")
    if not isinstance(words, list) or not words:
        return []
    segments: list[tuple[int, int, str]] = []
    buffer: list[str] = []
    begin = None
    end = None
    for word in words:
        if not isinstance(word, dict):
            continue
        piece = _clean_text(word.get("text")) + _clean_text(word.get("punctuation"))
        if not piece:
            continue
        word_begin = _to_milliseconds(word.get("begin_time"))
        word_end = _to_milliseconds(word.get("end_time"))
        if begin is None:
            begin = word_begin
        pending = "".join(buffer) + piece
        too_long = len(pending) > max_chars
        too_slow = end is not None and word_end - begin > max_milliseconds
        if buffer and (too_long or too_slow):
            segments.append((begin, end if end is not None else word_begin, "".join(buffer)))
            buffer = [piece]
            begin = word_begin
        else:
            buffer.append(piece)
        end = max(word_end, begin)
        # 词尾标点通常是自然停顿点，优先在此收尾。
        if piece.strip() and piece.strip()[-1] in _BREAK_PUNCTUATION and len("".join(buffer)) >= max_chars // 2:
            segments.append((begin, end, "".join(buffer)))
            buffer = []
            begin = None
            end = None
    if buffer and begin is not None:
        segments.append((begin, end if end is not None else begin, "".join(buffer)))
    return [(start, max(stop, start), text) for start, stop, text in segments if text]


def normalize_cues(
    sentences: Optional[Iterable],
    *,
    max_characters: int = MAX_CUE_CHARS,
    max_seconds: float = MAX_CUE_SECONDS,
) -> list[tuple[int, int, str]]:
    """把 DashScope 的 sentences 结构规范化成 (起点, 终点, 文本) 列表。"""
    if not sentences or not isinstance(sentences, (list, tuple)):
        return []
    max_characters = max(1, int(max_characters))
    max_milliseconds = max(1, int(max_seconds * 1000))
    cues: list[tuple[int, int, str]] = []
    for sentence in sentences:
        if not isinstance(sentence, dict):
            continue
        text = _clean_text(sentence.get("text"))
        begin = _to_milliseconds(sentence.get("begin_time"))
        end = max(_to_milliseconds(sentence.get("end_time")), begin)
        if not text:
            continue
        if len(text) <= max_characters and end - begin <= max_milliseconds:
            cues.append((begin, end, text))
            continue
        segments = _segment_by_words(sentence, max_characters, max_milliseconds)
        if segments:
            cues.extend(segments)
        else:
            # 没有词级时间时不做猜测性切分，保留整句以免丢字。
            cues.append((begin, end, text))
    # 保证时间单调，避免播放器出现时间倒流。
    ordered: list[tuple[int, int, str]] = []
    previous_end = 0
    for begin, end, text in cues:
        begin = max(begin, previous_end)
        end = max(end, begin)
        ordered.append((begin, end, text))
        previous_end = end
    return ordered


def to_srt(sentences: Optional[Sequence], **kwargs) -> Optional[str]:
    """生成 SRT 文本；没有可用时间戳时返回 ``None``。"""
    cues = normalize_cues(sentences, **kwargs)
    if not cues:
        return None
    blocks = []
    for index, (begin, end, text) in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{format_timestamp(begin)} --> {format_timestamp(end)}\n{text}"
        )
    return "\n\n".join(blocks) + "\n"
