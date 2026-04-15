import json
import os
import getpass
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

FILE_NAME = "vault.enc"
SALT_FILE = "salt.bin"

def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,          # 256-bit key for AES
        salt=salt,
        iterations=1000000, # Very secure (high iterations)
    )
    return kdf.derive(master_password.encode())

def load_or_create_salt():
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()
    else:
        salt = os.urandom(16)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
        return salt

def encrypt_data(data: dict, key: bytes) -> bytes:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(data).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext

def decrypt_data(encrypted: bytes, key: bytes) -> dict:
    aesgcm = AESGCM(key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode())

def main():
    print("Welcome to SyntecXHub Password Manager")
    
    salt = load_or_create_salt()
    
    while True:
        master_pass = getpass.getpass("Enter Master Password: ")
        key = derive_key(master_pass, salt)
        
        if not os.path.exists(FILE_NAME):
            print("First time setup! Creating new vault...")
            vault = {"entries": []}
            encrypted = encrypt_data(vault, key)
            with open(FILE_NAME, "wb") as f:
                f.write(encrypted)
            print("Vault created successfully!\n")
            break
        else:
            try:
                with open(FILE_NAME, "rb") as f:
                    encrypted = f.read()
                vault = decrypt_data(encrypted, key)
                print("Vault unlocked successfully!\n")
                break
            except:
                print("Wrong Master Password! Try again.\n")
    
    while True:
        print("\n=== MENU ===")
        print("1. Add New Password")
        print("2. View All Passwords")
        print("3. Search Password")
        print("4. Delete Password")
        print("5. Exit")
        
        choice = input("Choose option (1-5): ").strip()
        
        if choice == "1":
            site = input("Website/App Name: ")
            username = input("Username/Email: ")
            password = getpass.getpass("Password: ")
            notes = input("Notes (optional): ")
            
            entry = {
                "site": site,
                "username": username,
                "password": password,
                "notes": notes
            }
            vault["entries"].append(entry)
            
            encrypted = encrypt_data(vault, key)
            with open(FILE_NAME, "wb") as f:
                f.write(encrypted)
            print("Password added and encrypted!")
            
        elif choice == "2":
            if not vault["entries"]:
                print("No passwords saved yet.")
            else:
                print("\n=== ALL PASSWORDS ===")
                for i, entry in enumerate(vault["entries"], 1):
                    print(f"{i}. {entry['site']} | {entry['username']}")
        
        elif choice == "3":
            search = input("Search by Website/App Name: ").lower()
            found = [e for e in vault["entries"] if search in e["site"].lower()]
            if found:
                for e in found:
                    print(f"\nSite: {e['site']}")
                    print(f"Username: {e['username']}")
                    print(f"Password: {e['password']}")
                    print(f"Notes: {e['notes']}")
            else:
                print("No matching entries found.")
        
        elif choice == "4":
            if not vault["entries"]:
                print("No passwords to delete.")
                continue
            for i, entry in enumerate(vault["entries"], 1):
                print(f"{i}. {entry['site']}")
            try:
                idx = int(input("Enter number to delete: ")) - 1
                if 0 <= idx < len(vault["entries"]):
                    deleted = vault["entries"].pop(idx)
                    print(f"Deleted: {deleted['site']}")
                    encrypted = encrypt_data(vault, key)
                    with open(FILE_NAME, "wb") as f:
                        f.write(encrypted)
                else:
                    print("Invalid number.")
            except:
                print("Invalid input.")
        
        elif choice == "5":
            print("Exiting... Vault is securely encrypted on disk.")
            break

if __name__ == "__main__":
    main()