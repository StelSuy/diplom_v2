import base64
import logging
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


def verify_signature(public_key_b64: str, challenge_b64: str, signature_b64: str) -> bool:
    """
    public_key_b64  - base64 DER public key (як повертає Employee)
    challenge_b64   - base64 bytes challenge (термінал надсилає в base64)
    signature_b64   - base64 signature (як повертає Employee)

    ВИПРАВЛЕНО: розділено помилки підпису (очікувані) від помилок парсингу/ключа (неочікувані).
    """
    try:
        pub_bytes = base64.b64decode(public_key_b64)
        challenge = base64.b64decode(challenge_b64)
        signature = base64.b64decode(signature_b64)
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
