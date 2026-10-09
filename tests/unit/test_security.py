import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from argon2 import PasswordHasher

from app.core.config import ConfigError, Settings
from app.core.errors import AuthError
from app.core.security import (
    JWT_ISSUER,
    create_access_token,
    decode_access_token,
    dummy_password_hash,
    hash_password,
    needs_rehash,
    verify_password,
)

pytestmark = pytest.mark.unit

KEY = "k" * 40


def settings(**overrides: object) -> Settings:
    data: dict[str, object] = {"secret_key": KEY}
    return Settings(_env_file=None, **{**data, **overrides})  # type: ignore[arg-type]


def test_hash_and_verify() -> None:
    hashed = hash_password("Senha12345")
    assert hashed.startswith("$argon2id$")
    assert hashed != "Senha12345"
    assert verify_password(hashed, "Senha12345") is True
    assert verify_password(hashed, "senha12345") is False


def test_hash_is_salted() -> None:
    assert hash_password("Senha12345") != hash_password("Senha12345")


def test_verify_with_garbage_hash_is_false() -> None:
    assert verify_password("isto-nao-e-um-hash", "x") is False
    assert verify_password("", "x") is False


def test_needs_rehash_for_weaker_parameters() -> None:
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash("Senha12345")
    assert needs_rehash(weak) is True
    assert needs_rehash(hash_password("Senha12345")) is False


def test_dummy_hash_is_valid_but_never_matches_real_passwords() -> None:
    assert dummy_password_hash().startswith("$argon2id$")
    assert verify_password(dummy_password_hash(), "Senha12345") is False


def test_token_roundtrip_and_claims() -> None:
    user = uuid.uuid4()
    token = create_access_token(user, settings())
    assert decode_access_token(token, settings()) == user
    claims = jwt.decode(token, KEY, algorithms=["HS256"], issuer=JWT_ISSUER)
    assert set(claims) == {"sub", "iat", "exp", "iss", "jti"}
    assert claims["exp"] - claims["iat"] == 60 * 60


def test_each_token_has_unique_jti() -> None:
    user = uuid.uuid4()
    first = jwt.decode(
        create_access_token(user, settings()), KEY, algorithms=["HS256"], issuer=JWT_ISSUER
    )
    second = jwt.decode(
        create_access_token(user, settings()), KEY, algorithms=["HS256"], issuer=JWT_ISSUER
    )
    assert first["jti"] != second["jti"]


def encode(**overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": JWT_ISSUER,
        "jti": str(uuid.uuid4()),
    }
    claims.update(overrides)
    return jwt.encode(claims, KEY, algorithm="HS256")


def test_expired_token_is_rejected() -> None:
    with pytest.raises(AuthError):
        decode_access_token(encode(exp=datetime.now(UTC) - timedelta(seconds=5)), settings())


def test_wrong_issuer_is_rejected() -> None:
    with pytest.raises(AuthError):
        decode_access_token(encode(iss="outro-sistema"), settings())


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(uuid.uuid4(), settings())
    head, payload, signature = token.split(".")
    with pytest.raises(AuthError):
        decode_access_token(f"{head}.{payload}x.{signature}", settings())
    with pytest.raises(AuthError):
        decode_access_token(f"{head}.{payload}.{signature[:-3]}abc", settings())


def test_wrong_key_is_rejected() -> None:
    token = create_access_token(uuid.uuid4(), settings())
    with pytest.raises(AuthError):
        decode_access_token(token, settings(secret_key="z" * 40))


def test_alg_none_is_rejected() -> None:
    now = datetime.now(UTC)
    unsigned = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": JWT_ISSUER,
            "jti": "x",
        },
        key=None,
        algorithm="none",
    )
    with pytest.raises(AuthError):
        decode_access_token(unsigned, settings())


def test_other_hmac_algorithm_is_rejected() -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": JWT_ISSUER,
            "jti": "x",
        },
        KEY,
        algorithm="HS512",
    )
    with pytest.raises(AuthError):
        decode_access_token(token, settings())


@pytest.mark.parametrize("missing", ["sub", "exp", "iat", "iss", "jti"])
def test_missing_required_claim_is_rejected(missing: str) -> None:
    now = datetime.now(UTC)
    claims = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": JWT_ISSUER,
        "jti": "x",
    }
    del claims[missing]
    with pytest.raises(AuthError):
        decode_access_token(jwt.encode(claims, KEY, algorithm="HS256"), settings())


def test_subject_must_be_a_uuid() -> None:
    with pytest.raises(AuthError):
        decode_access_token(encode(sub="não-é-uuid"), settings())


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c", "Bearer x"])
def test_garbage_tokens(garbage: str) -> None:
    with pytest.raises(AuthError):
        decode_access_token(garbage, settings())


def test_without_secret_key_tokens_are_refused() -> None:
    empty = Settings(_env_file=None)  # type: ignore[call-arg]
    with pytest.raises(ConfigError, match="SECRET_KEY"):
        create_access_token(uuid.uuid4(), empty)
    with pytest.raises(ConfigError, match="SECRET_KEY"):
        decode_access_token("a.b.c", empty)
