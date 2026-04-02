import sqlite3
import os

db_path = "/mnt/c/Users/HP/OneDrive/Desktop/cems_v3/cems/cems/db.sqlite3"
env_path = "/mnt/c/Users/HP/OneDrive/Desktop/cems_v3/cems/cems/.env"

if not os.path.exists(db_path):
    print("Database not found at:", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Elevate all users to staff & superuser
c.execute("UPDATE auth_user SET is_staff=1, is_superuser=1")
print(f"✅ Users elevated to staff and superuser: {c.rowcount}")
conn.commit()

# 2. Get the first user's email to fix the .env file
c.execute("SELECT email FROM auth_user WHERE email != '' AND email IS NOT NULL LIMIT 1")
row = c.fetchone()
conn.close()

if row and row[0]:
    email = row[0]
    print(f"📧 Found user email: {email}")
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith('EMAIL_HOST_USER='):
                    f.write(f"EMAIL_HOST_USER={email}\n")
                elif line.startswith('DEFAULT_FROM_EMAIL='):
                    f.write(f"DEFAULT_FROM_EMAIL={email}\n")
                else:
                    f.write(line)
        print("✅ Fixed .env placeholders with the email address!")
    else:
        print("❌ .env file not found!")
else:
    print("❌ No valid email found in the database to fix the .env file. User needs to do it manually.")
