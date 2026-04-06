"""
Юніт-тести для app/security/verify.py

Перевіряють verify_signature() з реальними RSA-ключами, що генеруються
прямо в тесті — жодних залежностей від БД або сервера.
"""
import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.security.verify import verify_signature, _b64decode


# ─── Фікстури ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rsa_keypair():
    """Генерує RSA-2048 ключову пару один раз для всього модуля."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture(scope="module")
def public_key_b64(rsa_keypair):
    """DER-публічний ключ у Base64 (формат, який зберігає Employee HCE)."""
    _, public_key = rsa_keypair
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(der).decode()


def make_signature(private_key, challenge_bytes: bytes) -> str:
    """Підписує challenge приватним ключем — імітує Android KeyStore."""
    sig = private_key.sign(challenge_bytes, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


# ─── _b64decode ──────────────────────────────────────────────────────────────

class TestB64Decode:
    def test_standard_base64(self):
        original = b"hello world"
        encoded = base64.b64encode(original).decode()
        assert _b64decode(encoded) == original

    def test_url_safe_chars_converted(self):
        # secrets.token_urlsafe використовує - і _
        data = b"\xfb\xff\xfe"  # bytes that encode to +// in standard, -__ in urlsafe
        url_safe = base64.urlsafe_b64encode(data).decode()
        assert "-" in url_safe or "_" in url_safe
        assert _b64decode(url_safe) == data

    def test_missing_padding_handled(self):
        original = b"test"
        encoded = base64.b64encode(original).decode().rstrip("=")
        assert _b64decode(encoded) == original

    def test_empty_string_returns_empty_bytes(self):
        assert _b64decode("") == b""


# ─── verify_signature — happy path ───────────────────────────────────────────

class TestVerifySignatureValid:
    def test_valid_signature_returns_true(self, rsa_keypair, public_key_b64):
        private_key, _ = rsa_keypair
        challenge = b"server-challenge-abc123"
        challenge_b64 = base64.b64encode(challenge).decode()
        sig_b64 = make_signature(private_key, challenge)

        assert verify_signature(public_key_b64, challenge_b64, sig_b64) is True

    def test_valid_with_urlsafe_challenge(self, rsa_keypair, public_key_b64):
        """challenge від secrets.token_urlsafe() — може містити - і _"""
        private_key, _ = rsa_keypair
        import secrets
        token = secrets.token_urlsafe(32)
        challenge = token.encode()
        challenge_b64 = base64.b64encode(challenge).decode()
        sig_b64 = make_signature(private_key, challenge)

        assert verify_signature(public_key_b64, challenge_b64, sig_b64) is True

    def test_valid_with_binary_challenge(self, rsa_keypair, public_key_b64):
        private_key, _ = rsa_keypair
        challenge = bytes(range(32))
        challenge_b64 = base64.b64encode(challenge).decode()
        sig_b64 = make_signature(private_key, challenge)

        assert verify_signature(public_key_b64, challenge_b64, sig_b64) is True


# ─── verify_signature — bad signature ────────────────────────────────────────

class TestVerifySignatureInvalid:
    def test_wrong_signature_returns_false(self, rsa_keypair, public_key_b64):
        private_key, _ = rsa_keypair
        challenge = b"real-challenge"
        challenge_b64 = base64.b64encode(challenge).decode()

        # Підпис від іншого challenge
        wrong_sig_b64 = make_signature(private_key, b"other-challenge")

        assert verify_signature(public_key_b64, challenge_b64, wrong_sig_b64) is False

    def test_tampered_signature_returns_false(self, rsa_keypair, public_key_b64):
        private_key, _ = rsa_keypair
        challenge = b"challenge"
        challenge_b64 = base64.b64encode(challenge).decode()
        sig_b64 = make_signature(private_key, challenge)

        # Псуємо підпис: міняємо останні байти
        sig_bytes = base64.b64decode(sig_b64)
        tampered = sig_bytes[:-4] + bytes([b ^ 0xFF for b in sig_bytes[-4:]])
        tampered_b64 = base64.b64encode(tampered).decode()

        assert verify_signature(public_key_b64, challenge_b64, tampered_b64) is False

    def test_wrong_public_key_returns_false(self, rsa_keypair):
        private_key, _ = rsa_keypair

        # Генеруємо другу пару
        other_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        other_pub_der = other_private.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        other_pub_b64 = base64.b64encode(other_pub_der).decode()

        challenge = b"challenge"
        challenge_b64 = base64.b64encode(challenge).decode()
        sig_b64 = make_signature(private_key, challenge)  # підписано першим ключем

        assert verify_signature(other_pub_b64, challenge_b64, sig_b64) is False

    def test_empty_signature_returns_false(self, public_key_b64):
        challenge_b64 = base64.b64encode(b"challenge").decode()
        assert verify_signature(public_key_b64, challenge_b64, "") is False

    def test_garbage_public_key_returns_false(self):
        garbage_pub = base64.b64encode(b"this is not a DER key").decode()
        challenge_b64 = base64.b64encode(b"x").decode()
        sig_b64 = base64.b64encode(b"x").decode()
        assert verify_signature(garbage_pub, challenge_b64, sig_b64) is False

    def test_garbage_signature_bytes_returns_false(self, public_key_b64):
        challenge_b64 = base64.b64encode(b"challenge").decode()
        garbage_sig = base64.b64encode(b"\x00" * 64).decode()
        assert verify_signature(public_key_b64, challenge_b64, garbage_sig) is False
