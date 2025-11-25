import re
import requests
from typing import List, Tuple, Optional
import unittest
from pathlib import Path
from urllib.parse import urlparse
import html
import os


class SNILSValidator:
    """Класс для проверки и поиска синтаксически корректных СНИЛС."""

    # Улучшенное регулярное выражение для поиска СНИЛС в тексте
    SNILS_PATTERN = re.compile(
        r'(?<!\d)'  # Отрицательная lookbehind - не цифра перед началом
        r'(\d{3})'  # Первые 3 цифры (группа 1)
        r'[-\s]?'  # Необязательный разделитель
        r'(\d{3})'  # Следующие 3 цифры (группа 2)
        r'[-\s]?'  # Необязательный разделитель
        r'(\d{3})'  # Последние 3 цифры основного номера (группа 3)
        r'[-\s]?'  # Необязательный разделитель
        r'(\d{2})'  # Контрольное число (группа 4)
        r'(?!\d)'  # Отрицательная lookahead - не цифра после конца
    )

    # Альтернативное регулярное выражение для разных форматов
    SNILS_ALTERNATIVE_PATTERN = re.compile(
        r'(?<!\d)'  # Не цифра перед началом
        r'(\d{3})'  # Группа 1
        r'[-—\s]?'  # Разные типы разделителей
        r'(\d{3})'  # Группа 2
        r'[-—\s]?'  # Разные типы разделителей
        r'(\d{3})'  # Группа 3
        r'[-—\s]?'  # Разные типы разделителей
        r'(\d{2})'  # Группа 4
        r'(?!\d)'  # Не цифра после конца
    )

    @staticmethod
    def validate_checksum(snils: str) -> bool:
        """Проверка контрольной суммы СНИЛС."""
        if not snils.isdigit() or len(snils) != 11:
            return False

        number_part = snils[:9]
        checksum = int(snils[9:])

        total = 0
        for i, digit in enumerate(number_part, start=1):
            total += int(digit) * (10 - i)

        if total < 100:
            return checksum == total
        elif total == 100 or total == 101:
            return checksum == 0
        else:
            remainder = total % 101
            if remainder == 100:
                return checksum == 0
            else:
                return checksum == remainder

    def extract_snils_from_text(self, text: str, validate_checksum: bool = True) -> List[Tuple[str, str]]:
        """Извлечение СНИЛС из текста с использованием нескольких паттернов."""
        results = []
        found_normalized = set()  # Для избежания дубликатов

        # Используем оба паттерна для поиска
        patterns = [self.SNILS_PATTERN, self.SNILS_ALTERNATIVE_PATTERN]

        for pattern in patterns:
            for match in pattern.finditer(text):
                group1, group2, group3, checksum = match.groups()
                normalized = f"{group1}{group2}{group3}{checksum}"

                # Пропускаем дубликаты
                if normalized in found_normalized:
                    continue

                if not validate_checksum or self.validate_checksum(normalized):
                    formatted = f"{group1}-{group2}-{group3} {checksum}"
                    results.append((match.group(), formatted))
                    found_normalized.add(normalized)

        return results

    def get_snils_from_user_input(self) -> Optional[str]:
        """
        Получение и валидация СНИЛС от пользователя.
        """
        user_input = input("Введите СНИЛС: ").strip()
        matches = self.extract_snils_from_text(user_input, validate_checksum=True)

        if matches:
            _, normalized = matches[0]
            print(f"Корректный СНИЛС: {normalized}")
            return normalized.replace('-', '').replace(' ', '')
        else:
            print("СНИЛС не найден или невалиден")
            return None

    def get_snils_from_url(self, url: str, timeout: int = 10) -> List[Tuple[str, str]]:
        """
        Поиск СНИЛС на веб-странице.
        """
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = 'http://' + url

            print(f"Загрузка страницы: {url}")
            response = requests.get(
                url,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()

            print(f"Страница загружена успешно (статус: {response.status_code})")

            text = self._extract_text_from_html(response.text)
            print(f"Извлечено текста: {len(text)} символов")

            results = self.extract_snils_from_text(text, validate_checksum=True)
            print(f"Найдено СНИЛС: {len(results)}")

            return results

        except requests.exceptions.ConnectionError:
            print(f"Ошибка подключения к {url}. Сервер не доступен.")
            return []
        except requests.exceptions.Timeout:
            print(f"Таймаут при подключении к {url}")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"HTTP ошибка: {e}")
            return []
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return []

    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Базовое извлечение текста из HTML.
        """
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = html.unescape(text)
        text = ' '.join(text.split())
        return text

    def get_snils_from_file(self, file_path: str) -> List[Tuple[str, str]]:
        """
        Поиск СНИЛС в файле.
        """
        try:
            path = Path(file_path)

            if path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                return self.extract_snils_from_text(content)
            else:
                print(f"Формат {path.suffix} не поддерживается")
                return []

        except FileNotFoundError:
            print(f"Файл {file_path} не найден")
            return []
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []


class TestSNILSValidator(unittest.TestCase):
    """Тесты для валидатора СНИЛС."""

    def setUp(self):
        self.validator = SNILSValidator()

    def test_various_snils_formats(self):
        """Тестирование различных форматов СНИЛС."""
        test_cases = [
            ("112-233-445 95", 1),  # Стандартный формат
            ("11223344595", 1),  # Без разделителей
            ("112-233-44595", 1),  # Смешанный формат
            ("112 233 445 95", 1),  # С пробелами
            ("112—233—445 95", 1),  # С длинным тире
            ("СНИЛС:112-233-445 95", 1),  # После двоеточия
            ("№112-233-445 95", 1),  # После номера
        ]

        for input_text, expected_count in test_cases:
            with self.subTest(input_text=input_text):
                result = self.validator.extract_snils_from_text(input_text, validate_checksum=False)
                self.assertEqual(len(result), expected_count, f"Не найден СНИЛС: {input_text}")

    def test_multiple_snils_in_text(self):
        """Тест поиска нескольких СНИЛС в сложном тексте."""
        complex_text = """
        Сотрудники компании:
        1. Иванов Иван - СНИЛС: 112-233-445 95
        2. Петров Петр - СНИЛС:156-789-123 07  
        3. Сидорова Анна - СНИЛС 234-567-890 12
        4. Козлов Дмитрий - 345-678-901 23
        Контакты: тел.123-456-789, факс 987-654-321
        Не СНИЛС: 999-888-777 00 (невалидная контрольная сумма)
        """

        results = self.validator.extract_snils_from_text(complex_text, validate_checksum=True)
        self.assertEqual(len(results), 4, f"Должно быть найдено 4 СНИЛС, найдено {len(results)}")

    def test_snils_in_html_context(self):
        """Тест СНИЛС в HTML контексте."""
        html_text = """
        <div class="employee">
            <p>Иванов Иван</p>
            <p><strong>СНИЛС:</strong> 112-233-445 95</p>
            <p>Петров Петр - СНИЛС:156-789-123 07</p>
        </div>
        <span>234-567-890 12</span>
        """

        results = self.validator.extract_snils_from_text(html_text, validate_checksum=True)
        self.assertEqual(len(results), 3)

    def test_edge_cases(self):
        """Тест граничных случаев."""
        edge_cases = [
            ("112-233-44595 и 156-789-12307", 2),  # Два СНИЛС без пробелов
            ("11223344595 15678912307", 2),  # Два СНИЛС подряд
            ("Мой СНИЛС 112-233-445 95", 1),  # СНИЛС после текста
            ("112-233-445 95 мой номер", 1),  # СНИЛС перед текстом
        ]

        for text, expected_count in edge_cases:
            with self.subTest(text=text):
                results = self.validator.extract_snils_from_text(text, validate_checksum=False)
                self.assertEqual(len(results), expected_count)

    def test_invalid_formats(self):
        """Тест невалидных форматов."""
        invalid_cases = [
            "123-45-678 90",  # Неправильное количество цифр
            "12-345-678 90",  # Неправильное количество цифр
            "123-456-789",  # Нет контрольного числа
            "123-456-789 0",  # Неправильная длина контрольного числа
        ]

        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                result = self.validator.extract_snils_from_text(invalid_case)
                self.assertEqual(len(result), 0)


def test_snils_detection_comprehensive():
    """Комплексный тест обнаружения СНИЛС."""
    print("\n" + "=" * 70)
    print("КОМПЛЕКСНЫЙ ТЕСТ ОБНАРУЖЕНИЯ СНИЛС")
    print("=" * 70)

    validator = SNILSValidator()

    test_texts = [
        {
            "name": "Простой текст со СНИЛС",
            "text": "Мой СНИЛС: 112-233-445 95",
            "expected": 1
        },
        {
            "name": "Несколько СНИЛС в тексте",
            "text": "СНИЛСы: 112-233-445 95, 156-789-123 07, 234-567-890 12",
            "expected": 3
        },
        {
            "name": "СНИЛС в HTML",
            "text": "<p>СНИЛС: <b>112-233-445 95</b></p><span>156-789-123 07</span>",
            "expected": 2
        }
    ]

    for test in test_texts:
        print(f"\nТест: {test['name']}")
        print(f"Текст: {test['text'][:50]}...")

        results = validator.extract_snils_from_text(test['text'], validate_checksum=False)

        print(f"Найдено: {len(results)} (ожидалось: {test['expected']})")
        for i, (original, formatted) in enumerate(results, 1):
            print(f"   {i}. '{original}' -> {formatted}")

        if len(results) == test['expected']:
            print("Тест пройден!")
        else:
            print("Тест не пройден!")


def demonstrate_localhost_usage():
    """Демонстрация работы с локальным сервером 127.0.0.1:5000."""
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ С ЛОКАЛЬНЫМ СЕРВЕРОМ http://127.0.0.1:5000")
    print("=" * 70)

    validator = SNILSValidator()
    local_url = "http://127.0.0.1:5000"

    print(f"\nТестирование на локальном сервере: {local_url}")
    print("-" * 70)

    try:
        results = validator.get_snils_from_url(local_url, timeout=5)

        if results:
            print(f"\nНайдено СНИЛС: {len(results)}")
            for i, (original, formatted) in enumerate(results, 1):
                print(f"   {i}. {formatted}")
        else:
            print("\nСНИЛС не найдены")

    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    test_snils_detection_comprehensive()
    demonstrate_localhost_usage()

    print("\n" + "=" * 70)
    print("ЗАПУСК UNIT-ТЕСТОВ")
    print("=" * 70)

    unittest.main(argv=[''], verbosity=2, exit=False)