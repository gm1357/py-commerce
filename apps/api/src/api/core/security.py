from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()  # argon2

# Checked against when the email doesn't exist, so a failed login takes the same time either
# way and response timing can't reveal which emails have an account.
DUMMY_HASH = password_hash.hash("dummy-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)
