import hashlib
import json


def check_password(input_password: str) -> bool:
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        stored_hash = config.get("password_hash", "")

        input_hash = hashlib.sha256(input_password.encode()).hexdigest()

        return input_hash == stored_hash

    except Exception:
        return False
