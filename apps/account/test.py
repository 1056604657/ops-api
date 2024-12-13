import hashlib

password = "HS_Jdo@223"
hashed_password = hashlib.md5(password.encode()).hexdigest()
print(hashed_password)