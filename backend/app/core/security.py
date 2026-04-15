import bcrypt

DEFAULT_BCRYPT_ROUNDS = 12


def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    password_bytes = password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=rounds))
    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
