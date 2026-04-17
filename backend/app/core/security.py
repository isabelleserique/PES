from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Dict

import bcrypt

DEFAULT_BCRYPT_ROUNDS = 12
JWT_TYPE = "JWT"
JWT_ALGORITHM_HS256 = "HS256"


class InvalidTokenError(Exception):
    pass


class ExpiredTokenError(InvalidTokenError):
    pass


def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    password_bytes = password.encode("utf-8")
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=rounds))
    return password_hash.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
    *,
    payload: Dict[str, Any],
    secret_key: str,
    expires_delta: timedelta,
    algorithm: str = JWT_ALGORITHM_HS256,
) -> str:
    if algorithm != JWT_ALGORITHM_HS256:
        raise ValueError("Algoritmo JWT nao suportado.")

    now = datetime.now(UTC)
    token_payload = {
        **payload,
        "exp": int((now + expires_delta).timestamp()),
    }
    token_header = {
        "alg": algorithm,
        "typ": JWT_TYPE,
    }

    encoded_header = _encode_segment(token_header)
    encoded_payload = _encode_segment(token_payload)
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = _sign(signing_input=signing_input, secret_key=secret_key)

    return f"{signing_input}.{signature}"


def decode_access_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str = JWT_ALGORITHM_HS256,
) -> Dict[str, Any]:
    if algorithm != JWT_ALGORITHM_HS256:
        raise ValueError("Algoritmo JWT nao suportado.")

    token_parts = token.split(".")
    if len(token_parts) != 3:
        raise InvalidTokenError("Formato de token invalido.")

    encoded_header, encoded_payload, encoded_signature = token_parts
    signing_input = f"{encoded_header}.{encoded_payload}"

    header = _decode_segment(encoded_header)
    payload = _decode_segment(encoded_payload)

    if header.get("alg") != algorithm or header.get("typ") != JWT_TYPE:
        raise InvalidTokenError("Cabecalho JWT invalido.")

    expected_signature = _sign(signing_input=signing_input, secret_key=secret_key)
    if not hmac.compare_digest(encoded_signature, expected_signature):
        raise InvalidTokenError("Assinatura JWT invalida.")

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise InvalidTokenError("Claim exp invalida.")

    if datetime.now(UTC).timestamp() >= exp:
        raise ExpiredTokenError("Token expirado.")

    return payload


def _encode_segment(content: Dict[str, Any]) -> str:
    json_bytes = json.dumps(content, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(json_bytes)


def _decode_segment(segment: str) -> Dict[str, Any]:
    try:
        decoded_bytes = _base64url_decode(segment)
        decoded_json = json.loads(decoded_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidTokenError("Segmento JWT invalido.") from exc

    if not isinstance(decoded_json, dict):
        raise InvalidTokenError("Conteudo JWT invalido.")

    return decoded_json


def _sign(*, signing_input: str, secret_key: str) -> str:
    digest = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
