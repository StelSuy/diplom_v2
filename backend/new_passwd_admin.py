from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    bcrypt__rounds=12
)
new_hash = pwd_context.hash("admin")
print(new_hash)