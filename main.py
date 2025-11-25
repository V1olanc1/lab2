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

    # Регулярное выражение для поиска СНИЛС в тексте
    SNILS_PATTERN = re.compile(
        r'\b'  # Граница слова
        r'(\d{3})'  # Первые 3 цифры (группа 1)
        r'[-\s]?'  # Необязательный разделитель (- или пробел)
        r'(\d{3})'  # Следующие 3 цифры (группа 2)
        r'[-\s]?'  # Необязательный разделитель
        r'(\d{3})'  # Последние 3 цифры основного номера (группа 3)
        r'[-\s]?'  # Необязательный разделитель
        r'(\d{2})'  # Контрольное число (группа 4)
        r'\b'  # Граница слова
    )

    @staticmethod
    def validate_checksum(snils: str) -> bool:
        """Проверка контрольной суммы СНИЛС."""
        if not snils.isdigit() or len(snils) != 11:
            return False

        number_part = snils[:9]  # Основная часть (9 цифр)
        checksum = int(snils[9:])  # Контрольное число

        # Вычисление контрольной суммы
        total = 0
        for i, digit in enumerate(number_part, start=1):
            total += int(digit) * (10 - i)

        # Проверка контрольной суммы
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
        """Извлечение СНИЛС из текста."""
        results = []

        for match in self.SNILS_PATTERN.finditer(text):
            group1, group2, group3, checksum = match.groups()
            normalized = f"{group1}{group2}{group3}{checksum}"

            if not validate_checksum or self.validate_checksum(normalized):
                formatted = f"{group1}-{group2}-{group3} {checksum}"
                results.append((match.group(), formatted))

        return results

    def get_snils_from_user_input(self) -> Optional[str]:
        """Получение и валидация СНИЛС от пользователя."""
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
        """Поиск СНИЛС на веб-странице."""
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = 'http://' + url

            print(f"🔍 Загрузка страницы: {url}")
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
        """Базовое извлечение текста из HTML."""
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = html.unescape(text)
        text = ' '.join(text.split())
        return text

    def get_snils_from_file(self, file_path: str) -> List[Tuple[str, str]]:
        """Поиск СНИЛС в файле."""
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

    def test_valid_snils_formats(self):
        test_cases = [
            ("123-456-789 00", "12345678900"),
            ("12345678900", "12345678900"),
            ("123-456-78900", "12345678900"),
            ("123 456 789 00", "12345678900"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.validator.extract_snils_from_text(input_text, validate_checksum=False)
                self.assertEqual(len(result), 1)
                _, formatted = result[0]
                normalized = formatted.replace('-', '').replace(' ', '')
                self.assertEqual(normalized, expected)

    def test_invalid_snils_formats(self):
        invalid_cases = [
            "123-45-678 90",
            "12-345-678 90",
            "abc-def-ghi jk",
            "123-456-789",
            "123-456-789 0",
        ]

        for invalid_case in invalid_cases:
            with self.subTest(invalid_case=invalid_case):
                result = self.validator.extract_snils_from_text(invalid_case)
                self.assertEqual(len(result), 0)

    def test_checksum_validation(self):
        valid_snils = ["112-233-445 95", "156-789-123 07"]
        invalid_snils = ["112-233-445 00", "156-789-123 99"]

        for snils in valid_snils:
            with self.subTest(valid_snils=snils):
                result = self.validator.extract_snils_from_text(snils, validate_checksum=True)
                self.assertEqual(len(result), 1)

        for snils in invalid_snils:
            with self.subTest(invalid_snils=snils):
                result = self.validator.extract_snils_from_text(snils, validate_checksum=True)
                self.assertEqual(len(result), 0)

    def test_url_parsing(self):
        with unittest.mock.patch('requests.get') as mock_get:
            mock_response = unittest.mock.Mock()
            mock_response.text = """
            <html>
                <body>
                    <p>СНИЛС: 112-233-445 95</p>
                    <p>Другой СНИЛС: 156-789-123 07</p>
                </body>
            </html>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            results = self.validator.get_snils_from_url("http://127.0.0.1:5000")
            self.assertEqual(len(results), 2)


def demonstrate_localhost_usage():
    print("\n" + "=" * 70)
    print("ДЕМОНСТРАЦИЯ РАБОТЫ С ЛОКАЛЬНЫМ СЕРВЕРОМ http://127.0.0.1:5000")
    print("=" * 70)

    validator = SNILSValidator()
    local_url = "http://127.0.0.1:5000"

    print(f"\nТестирование на локальном сервере: {local_url}")

    try:
        results = validator.get_snils_from_url(local_url, timeout=5)

        if results:
            print(f"\nНа локальном сервере найдено СНИЛС: {len(results)}")
            print("\nНайденные СНИЛС:")
            for i, (original, formatted) in enumerate(results, 1):
                print(f"   {i}. {formatted}")
        else:
            print("\nНа локальном сервере СНИЛС не найдены")

    except Exception as e:
        print(f"\n💥 Ошибка при работе с локальным сервером: {e}")


def run_complete_demonstration():
    """Полная демонстрация работы системы."""
    validator = SNILSValidator()

    print("=== ПОЛНАЯ ДЕМОНСТРАЦИЯ СИСТЕМЫ ПОИСКА СНИЛС ===\n")

    # 1. Демонстрация с текстом
    print("1.ПОИСК В ТЕКСТЕ:")
    sample_text = """
    Отчет по сотрудникам:
    - Иванов И.И.: СНИЛС 112-233-445 95
    - Петров П.П.: СНИЛС 156-789-123 07  
    - Невалидный: 123-456-789 00
    """
    results = validator.extract_snils_from_text(sample_text)
    print(f"   Найдено: {len(results)} СНИЛС\n")

    # 2. Демонстрация с локальным сервером
    print("2.ПОИСК НА ЛОКАЛЬНОМ СЕРВЕРЕ:")
    demonstrate_localhost_usage()

    # 3. Демонстрация с файлом
    print("\n3.ПОИСК В ФАЙЛЕ:")
    with open('test_demo.txt', 'w', encoding='utf-8') as f:
        f.write("Файл с СНИЛС: 112-233-445 95 и 156-789-123 07")

    file_results = validator.get_snils_from_file('test_demo.txt')
    print(f"   Найдено в файле: {len(file_results)} СНИЛС")

    # Очистка
    if os.path.exists('test_demo.txt'):
        os.remove('test_demo.txt')


if __name__ == "__main__":
    run_complete_demonstration()

    print("\n" + "=" * 70)
    print("ЗАПУСК UNIT-ТЕСТОВ")
    print("=" * 70)

    # Запуск unit-тестов
    unittest.main(argv=[''], verbosity=2, exit=False)