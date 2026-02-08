"""
簡繁中文轉換工具
統一使用繁體中文（正體中文）作為系統輸出語言。
所有中文輸出（AI 回覆、語音識別、數據庫存儲）都必須經過此模組轉換。
"""
from opencc import OpenCC

# s2t = Simplified to Traditional (簡體 → 繁體)
_s2t = OpenCC('s2t')

# t2s = Traditional to Simplified (繁體 → 簡體，用於檢測)
_t2s = OpenCC('t2s')


def to_traditional(text: str) -> str:
    """將簡體中文轉換為繁體中文。已是繁體的文字不受影響。"""
    if not text:
        return text
    return _s2t.convert(text)


def to_simplified(text: str) -> str:
    """將繁體中文轉換為簡體中文。僅用於檢測目的。"""
    if not text:
        return text
    return _t2s.convert(text)


def has_simplified(text: str) -> bool:
    """
    檢測文本中是否包含簡體字。
    原理：將文本轉繁體後比對，如果有差異則說明原文含簡體。
    """
    if not text:
        return False
    converted = _s2t.convert(text)
    return converted != text
