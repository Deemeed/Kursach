import hashlib
import json
import os


def check_password(input_password: str) -> bool:
    """Проверяет пароль по хэшу из config.json"""
    try:
        # Читаем config.json
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        # Получаем хэш из конфига
        stored_hash = config.get("password_hash", "")

        # Хэшируем введенный пароль
        input_hash = hashlib.sha256(input_password.encode()).hexdigest()

        # Сравниваем хэши
        return input_hash == stored_hash

    except Exception:
        return False