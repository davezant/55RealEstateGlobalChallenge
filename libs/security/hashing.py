from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hash = PasswordHash((Argon2Hasher(),))

def create_hash(string: str) -> str:
  return password_hash.hash(string)

def verify_if_hash_correct(plain_password: str, hashed_password: str) -> bool:
  return password_hash.verify(plain_password, hashed_password)
