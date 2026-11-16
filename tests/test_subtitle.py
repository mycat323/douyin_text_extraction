"""SRT 字幕生成的离线测试。"""
from src.subtitle import format_timestamp, normalize_cues, to_srt


def _sentence(begin, end, text, words=None):
    sentence = {"begin_time": begin, "end_time": end, "text": text}
    if words is not None:
        sentence["words"] = words
    return sentence


def test_format_timestamp_pads_and_handles_hours():
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(1) == "00:00:00,001"
    assert format_timestamp(61_500) == "00:01:01,500"
    assert format_timestamp(3_661_007) == "01:01:01,007"


def test_format_timestamp_clamps_invalid_values():
    for value in (None, "", "abc", -5, float("nan"), float("inf")):
        assert format_timestamp(value) == "00:00:00,000"


def test_to_srt_numbers_cues_and_uses_crlf_free_layout():
    srt = to_srt([
        _sentence(100, 3820, "Hello word, 这里是阿里巴巴语音实验室。"),
        _sentence(3820, 6000, "第二句。"),
    ])
    assert srt == (
        "1\n00:00:00,100 --> 00:00:03,820\nHello word, 这里是阿里巴巴语音实验室。\n"
        "\n"
        "2\n00:00:03,820 --> 00:00:06,000\n第二句。\n"
    )


def test_to_srt_returns_none_without_sentences():
    assert to_srt(None) is None
    assert to_srt([]) is None
    assert to_srt([_sentence(0, 1000, "   ")]) is None
    assert to_srt("not a list") is None


def test_cue_text_is_flattened_to_single_line():
    srt = to_srt([_sentence(0, 1000, "第一行\n第二行\r\n第三行")])
    assert "\n\n1\n" not in srt.split("\n\n")[0]
    assert "第一行 第二行 第三行" in srt


def test_long_sentence_is_split_on_word_boundaries(monkeypatch):
    import src.subtitle as subtitle

    monkeypatch.setattr(subtitle, "MAX_CUE_CHARS", 6)
    words = [
        {"begin_time": i * 500, "end_time": (i + 1) * 500, "text": character, "punctuation": ""}
        for i, character in enumerate("一二三四五六七八九十")
    ]
    cues = normalize_cues([_sentence(0, 5000, "一二三四五六七八九十", words)], max_characters=6)
    assert len(cues) > 1
    assert "".join(text for _, _, text in cues) == "一二三四五六七八九十"
    assert all(len(text) <= 6 for _, _, text in cues)


def test_time_is_monotonic_across_sentences():
    cues = normalize_cues([
        _sentence(0, 2000, "第一句"),
        _sentence(500, 1500, "时间重叠的第二句"),
        _sentence(1000, 1000, "零长度"),
    ])
    assert [begin for begin, _, _ in cues] == sorted(begin for begin, _, _ in cues)
    for begin, end, _ in cues:
        assert end >= begin


def test_malformed_sentences_are_skipped():
    cues = normalize_cues([
        None,
        "string",
        {"begin_time": 0, "end_time": 1000},
        _sentence(0, 1000, "有效文本"),
    ])
    assert cues == [(0, 1000, "有效文本")]


def test_words_without_punctuation_still_produce_text():
    cues = normalize_cues([_sentence(0, 2000, "甲 乙", [
        {"begin_time": 0, "end_time": 1000, "text": "甲"},
        {"begin_time": 1000, "end_time": 2000, "text": "乙"},
    ])], max_characters=1)
    assert "".join(text for _, _, text in cues) == "甲乙"
