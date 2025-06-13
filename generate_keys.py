import sys
import getpass
from streamlit_authenticator.utilities.hasher import Hasher

# A simple script to hash passwords for the config.yaml file.
# This version is corrected for streamlit-authenticator v0.4.2.

print("--- Hashed Password Generator (v0.4.2) ---")
print("Enter passwords to hash. Press Enter on an empty line to finish.")

passwords_to_hash = []
while True:
    try:
        password = getpass.getpass(f"Enter password {len(passwords_to_hash) + 1} (input hidden): ")
        if not password:
            break
        passwords_to_hash.append(password)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)

if not passwords_to_hash:
    print("No passwords were entered. Exiting.")
    sys.exit(0)

try:
    # This is the correct syntax for v0.4.2.
    hashed_passwords = Hasher().generate(passwords_to_hash)
    
    print("\n--- Generated Hashed Passwords ---")
    for i, hashed_pw in enumerate(hashed_passwords):
        print(f"Hash for password {i+1}: {hashed_pw}")
    print("\nCopy the generated hash(es) into your config.yaml file.")

except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    print("Please ensure 'streamlit-authenticator' and 'bcrypt' are installed correctly.")