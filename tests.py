import re

import pytest
import requests

from main import (
    compute_snils_checksum,
    find_snils_in_file,
    find_snils_in_text,
    find_snils_in_url,
    format_checksum_as_two_digits,
    is_valid_snils,
    normalize_digits,
)


def test_normalize_digits_and_basic_valid():
    assert normalize_digits("112-233-445 95") == "11223344595"
    assert is_valid_snils("112-233-445 95") is True
    assert is_valid_snils("11223344595") is True


def test_compute_checksum_examples():
    nine = "112233445"
    assert compute_snils_checksum(nine) == 95


def test_is_valid_with_generated():
    nine = "100000000"
    cs = compute_snils_checksum(nine)
    sn = nine + format_checksum_as_two_digits(cs)
    assert is_valid_snils(sn)

    for i in range(100000000, 100000000 + 20000):
        s = str(i)
        try:
            val = compute_snils_checksum(s)
        except ValueError:
            continue

        sn_candidate = s + format_checksum_as_two_digits(val)
        assert is_valid_snils(sn_candidate)

        if i - 100000000 > 500:
            break


def test_find_snils_in_text_and_file(tmp_path):
    text = (
        "В тексте есть номер 112-233-445 95 и ещё какой-то текст "
        "и 12345678901."
    )

    found = find_snils_in_text(text)
    assert any(
        "112-233-445 95" in item[0] or "11223344595" in item[0]
        for item in found
    )

    p = tmp_path / "f.txt"
    p.write_text(text, encoding="utf-8")

    found2 = find_snils_in_file(str(p))
    assert len(found2) >= 1


def test_find_snils_in_local_server():
    url = "http://127.0.0.1:5000"

    try:
        found = find_snils_in_url(url)
    except requests.exceptions.ConnectionError:
        pytest.skip(
            "Локальный сервер не запущен. Запустите server.py перед тестом"
        )

    valid_expected = {
        "11223344595",
        "15678912307",
        "23456789012",
    }

    found_digits = {re.sub(r"\D", "", x[0]) for x in found}

    assert valid_expected.issubset(found_digits), (
        f"Не найдены СНИЛС: {valid_expected - found_digits}"
    )

    assert len(found_digits) >= 3, (
        f"Найдено только {len(found_digits)} СНИЛС: {found_digits}"
    )
