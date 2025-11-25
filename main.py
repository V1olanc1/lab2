import re
import requests
from typing import List, Tuple, Optional
from pathlib import Path


class SNILSValidator:
    """Класс для валидации и поиска СНИЛС в различных источниках."""
    # Регулярное выражение для поиска СНИЛС
    SNILS_PATTERN = re.compile(
        r'\b(\d{3})-(\d{3})-(\d{3})\s*(\d{2})\b',
        re.IGNORECASE
    )

    # Регулярное выражение для строгой валидации (только корректные СНИЛС)
    STRICT_SNILS_PATTERN = re.compile(
        r'^\s*(\d{3})-(\d{3})-(\d{3})\s+(\d{2})\s*$',
        re.IGNORECASE
    )

    @staticmethod
    def calculate_checksum(snils_number: str) -> str:
        """Вычисляет контрольную сумму для СНИЛС."""
        if len(snils_number) != 9 or not snils_number.isdigit():
            raise ValueError("SNILS number must be exactly 9 digits")

        total = 0
        for i, digit in enumerate(snils_number):
            total += int(digit) * (9 - i)

        if total < 100:
            return f"{total:02d}"
        elif total == 100 or total == 101:
            return "00"
        else:
            remainder = total % 101
            if remainder == 100:
                return "00"
            else:
                return f"{remainder:02d}"

    @staticmethod
    def validate_snils(snils: str) -> bool:
        """Проверяет корректность СНИЛС включая контрольную сумму."""
        match = SNILSValidator.STRICT_SNILS_PATTERN.match(snils)
        if not match:
            return False

        number_part = ''.join(match.groups()[:3])
        checksum = match.group(4)

        try:
            calculated_checksum = SNILSValidator.calculate_checksum(number_part)
            return checksum == calculated_checksum
        except ValueError:
            return False

    @staticmethod
    def extract_snils_from_text(text: str, validate_checksum: bool = True) -> List[str]:
        """Извлекает СНИЛС из текста."""
        matches = SNILSValidator.SNILS_PATTERN.findall(text)
        result = []

        for match in matches:
            number_part = ''.join(match[:3])
            checksum = match[3]
            snils_str = f"{match[0]}-{match[1]}-{match[2]} {checksum}"

            if validate_checksum:
                try:
                    calculated_checksum = SNILSValidator.calculate_checksum(number_part)
                    if checksum == calculated_checksum:
                        result.append(snils_str)
                except ValueError:
                    continue
            else:
                result.append(snils_str)

        return result

    @staticmethod
    def find_snils_in_file(file_path: str, validate_checksum: bool = True) -> List[str]:
        """Ищет СНИЛС в файле."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return SNILSValidator.extract_snils_from_text(content, validate_checksum)
        except UnicodeDecodeError:
            for encoding in ['cp1251', 'iso-8859-1', 'windows-1251']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        return SNILSValidator.extract_snils_from_text(content, validate_checksum)
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Не удалось расшифровать файл {file_path} в какой-либо поддерживаемой кодировке")

    @staticmethod
    def find_snils_on_webpage(url: str, validate_checksum: bool = True) -> List[str]:
        """Ищет СНИЛС на веб-странице."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return SNILSValidator.extract_snils_from_text(response.text, validate_checksum)
        except requests.RequestException as e:
            raise ConnectionError(f"Не удалось получить доступ к веб-странице: {e}")

    @staticmethod
    def get_user_input() -> List[str]:
        """Получает СНИЛС от пользователя через консольный ввод."""
        print("Введите СНИЛС в формате XXX-XXX-XXX YY (пустая строка для завершения):")
        snils_list = []

        while True:
            try:
                user_input = input("СНИЛС: ").strip()
                if not user_input:
                    break

                if SNILSValidator.validate_snils(user_input):
                    snils_list.append(user_input)
                    print("Корректный СНИЛС")
                else:
                    print("Некорректный СНИЛС")
            except KeyboardInterrupt:
                print("\nВвод прерван")
                break

        return snils_list