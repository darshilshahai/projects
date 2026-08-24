from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


class PasswordService:
    def hash_password(self, password: str) -> str:
        return _hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        return _hasher.verify(password, password_hash)
