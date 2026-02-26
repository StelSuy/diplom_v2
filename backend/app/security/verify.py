import base64
import logging
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


def _b64decode(s: str) -> bytes:
    """Декодирует Base64/Base64url, устойчиво к отсутствию padding '='."""
    # Заменяем URL-safe символы на стандартные
    s = s.replace('-', '+').replace('_', '/')
    # Добавляем недостающий padding
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)


def verify_signature(public_key_b64: str, challenge_b64: str, signature_b64: str) -> bool:
    """
    public_key_b64  - base64 DER public key (як повертає Employee)
    challenge_b64   - base64 bytes challenge (термінал надсилає в base64)
    signature_b64   - base64 signature (як повертає Employee)
    """
    try:
        pub_bytes = _b64decode(public_key_b64)
        challenge = _b64decode(challenge_b64)
        signature = _b64decode(signature_b64)
        public_key = serialization.load_der_public_key(pub_bytes)
    except Exception as e:
        logger.warning(f"verify_signature: failed to decode inputs: {e}")
        return False

    try:
        public_key.verify(
            signature,
            challenge,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        logger.warning(f"verify_signature: unexpected crypto error: {e}")
        return False