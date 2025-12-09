import bcrypt

new_password = "Timesheet@123"  # <-- your NEW password here
hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
print(hashed)
