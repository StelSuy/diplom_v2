import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def verify_signature(public_key_b64: str, challenge_b64: str, signature_b64: str) -> bool:
    """
    public_key_b64  - base64 DER public key (как отдаёт Employee)
    challenge_b64   - base64 bytes challenge (терминал отправляет в base64)
    signature_b64   - base64 signature (как отдаёт Employee)
    """
    try:
        pub_bytes = base64.b64decode(public_key_b64)
        challenge = base64.b64decode(challenge_b64)
        signature = base64.b64decode(signature_b64)

        public_key = serialization.load_der_public_key(pub_bytes)

        public_key.verify(
            signature,
            challenge,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False
