from __future__ import annotations

import re
from typing import List, Tuple, Optional

import requests

SNILS_SEARCH_RE = re.compile(
    r"""
    (?:
        (?:\d{3}[-\s]?){2}\d{3}[-\s]?\d{2}   # формат с разделителями или без
      |
        \b\d{11}\b                           # 11 подряд цифр
    )
    """,
    re.VERBOSE,
)


def normalize_digits(snils_like: str) -> str:
    """Убирает из переданной строки всё, кроме цифр, и возвращает строку из цифр."""
    return re.sub(r"\D", "", snils_like)


def compute_snils_checksum(nine_digits: str) -> int:
    """Вычисляет контрольное число (как целое 0..100) для первых 9 цифр."""
    if len(nine_digits) != 9 or not nine_digits.isdigit():
        raise ValueError("Требуется строка ровно из 9 цифр для вычисления контрольной суммы.")
    weights = list(range(9, 0, -1))  # [9,8,7,...,1]
    s = sum(int(d) * w for d, w in zip(nine_digits, weights))
    if s < 100:
        return s
    if s in (100, 101):
        return 0
    return s % 101


def format_checksum_as_two_digits(checksum: int) -> str:
    """Форматирует контрольное число как две цифры с ведущим нулём при необходимости."""
    if not (0 <= checksum <= 100):
        raise ValueError("Контрольное число должно быть в диапазоне 0..100.")
    return f"{checksum:02d}"


def is_valid_snils(snils_digits: str) -> bool:
    # snils_digits — только цифры, длиной 11
    if len(snils_digits) != 11 or not snils_digits.isdigit():
        return False

    body = snils_digits[:9]
    checksum = int(snils_digits[9:])

    total = sum(int(body[i]) * (9 - i) for i in range(9))

    if total < 100:
        expected = total
    elif total == 100 or total == 101:
        expected = 0
    else:
        expected = total % 101
        if expected == 100:
            expected = 0

    return checksum == expected


def find_snils_in_text(text: str) -> List[Tuple[str, int, int]]:
    """Ищет все потенциальные СНИЛС в переданном тексте и возвращает список кортежей:"""
    results: List[Tuple[str, int, int]] = []
    for m in SNILS_SEARCH_RE.finditer(text):
        candidate = m.group(0)
        if is_valid_snils(candidate):
            results.append((candidate, m.start(), m.end()))
    return results


def find_snils_in_file(path: str, encoding: str = "utf-8") -> List[Tuple[str, int, int]]:
    """Читает файл по указанному пути и ищет в нём СНИЛС."""
    with open(path, "r", encoding=encoding, errors="ignore") as f:
        text = f.read()
    return find_snils_in_text(text)


def find_snils_in_url(url: str):
    pattern = re.compile(
        r"\b\d{3}[- ]?\d{3}[- ]?\d{3}[- ]?\d{2}\b"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    text = response.text
    matches = pattern.findall(text)

    result = []
    for m in matches:
        digits = re.sub(r"\D", "", m)
        if is_valid_snils(digits):
            result.append((m, digits))

    return result


if __name__ == "__main__":
    print("Пример проверки СНИЛС. Введите СНИЛС (например, 112-233-445 95 или 11223344595):")
    s = input().strip()
    print("Введено:", s)
    print("Валиден?" , is_valid_snils(s))
