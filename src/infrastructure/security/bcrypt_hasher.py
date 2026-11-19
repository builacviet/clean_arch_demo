import hashlib


class SimplePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return hashlib.sha256(plain_password.encode()).hexdigest()
