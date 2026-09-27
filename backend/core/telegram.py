import hashlib
import hmac
import json
import re
import time
from urllib.parse import parse_qsl


class InvalidTelegramData(ValueError):
    def __init__(self, reason: str, *, age_seconds: int | None = None):
        super().__init__("Invalid or expired Telegram data")
        self.reason = reason
        self.age_seconds = age_seconds


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> int:
    """Return the Telegram user ID only after signature and freshness checks."""
    try:
        if re.search(r"%(?![0-9a-fA-F]{2})", init_data):
            raise ValueError("Invalid encoding")
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True,
                          encoding="utf-8", errors="strict", max_num_fields=32)
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError("Duplicate fields")
        received_hash = fields.pop("hash")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", received_hash):
            raise ValueError("Invalid hash")
        # For bot-token HMAC validation, exclude only hash (include signature
        # when present). Telegram's public-key validation uses different rules.
        check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash.lower()):
            raise InvalidTelegramData("signature_mismatch")
        auth_date = int(fields["auth_date"])
        age = time.time() - auth_date
        if age < -30:
            raise InvalidTelegramData("auth_date_in_future", age_seconds=int(age))
        if age > max_age_seconds:
            raise InvalidTelegramData("expired", age_seconds=int(age))
        user = json.loads(fields["user"])
        if not isinstance(user, dict):
            raise ValueError("Invalid user")
        user_id = user.get("id")
        if type(user_id) is not int or not 0 < user_id <= 2**63 - 1:
            raise ValueError("Invalid user ID")
        return user_id
    except InvalidTelegramData:
        raise
    except (ValueError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
        raise InvalidTelegramData("malformed_data") from exc
