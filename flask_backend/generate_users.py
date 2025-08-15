#!/usr/bin/env python3
"""
User Generation Script for AI Assistant
Generates secure usernames and passwords for the authentication system.
"""

import secrets
import string
import json
import os
import hashlib
import sqlite3
from typing import List, Dict, Tuple
from pathlib import Path

class UserGenerator:
    def __init__(self, db_path: str = "app/app.db"):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Ensure the database and users table exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_username(self, prefix: str = "user") -> str:
        """Generate a random username"""
        # Generate 6 random alphanumeric characters
        random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return f"{prefix}_{random_part}"
    
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        # Ensure at least one character from each category
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*"
        
        # Generate password with at least one of each type
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: str = None) -> bool:
        """Create a new user in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', (username, password_hash, email))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"User '{username}' already exists!")
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def generate_single_user(self, custom_username: str = None, custom_password: str = None) -> Dict:
        """Generate a single user with optional custom credentials"""
        username = custom_username or self.generate_username()
        password = custom_password or self.generate_password()
        
        success = self.create_user(username, password)
        
        return {
            "username": username,
            "password": password,
            "created": success
        }
    
    def generate_multiple_users(self, count: int = 5) -> List[Dict]:
        """Generate multiple users"""
        users = []
        for i in range(count):
            user = self.generate_single_user()
            users.append(user)
            print(f"Generated user {i+1}/{count}: {user['username']} - {user['password']}")
        return users
    
    def list_users(self) -> List[Dict]:
        """List all users in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, email, created_at, is_active FROM users')
        users = cursor.fetchall()
        
        conn.close()
        
        return [
            {
                "username": user[0],
                "email": user[1],
                "created_at": user[2],
                "is_active": bool(user[3])
            }
            for user in users
        ]
    
    def delete_user(self, username: str) -> bool:
        """Delete a user from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                print(f"User '{username}' deleted successfully.")
            else:
                print(f"User '{username}' not found.")
            
            return deleted
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def save_credentials_to_file(self, users: List[Dict], filename: str = "user_credentials.json"):
        """Save user credentials to a JSON file"""
        # Remove password hashes for security
        safe_users = []
        for user in users:
            safe_user = user.copy()
            if 'password_hash' in safe_user:
                del safe_user['password_hash']
            safe_users.append(safe_user)
        
        with open(filename, 'w') as f:
            json.dump(safe_users, f, indent=2)
        
        print(f"User list saved to {filename}")

def main():
    """Main function to run the user generator"""
    generator = UserGenerator()
    
    print("=== AI Assistant User Generator ===\n")
    
    while True:
        print("\nOptions:")
        print("1. Generate a single user")
        print("2. Generate multiple users")
        print("3. Create user with custom credentials")
        print("4. List all users")
        print("5. Delete a user")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            user = generator.generate_single_user()
            print(f"\nGenerated user:")
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print(f"Created: {'Yes' if user['created'] else 'No'}")
        
        elif choice == "2":
            try:
                count = int(input("How many users to generate? (default 5): ") or "5")
                users = generator.generate_multiple_users(count)
                print(f"\nGenerated {len(users)} users successfully!")
                
                # Save to file
                save = input("Save credentials to file? (y/n): ").lower().strip()
                if save == 'y':
                    generator.save_credentials_to_file(users)
            
            except ValueError:
                print("Invalid number!")
        
        elif choice == "3":
            username = input("Enter username: ").strip()
            password = input("Enter password (leave empty for random): ").strip()
            
            if not username:
                print("Username is required!")
                continue
            
            user = generator.generate_single_user(
                custom_username=username,
                custom_password=password if password else None
            )
            print(f"\nUser created:")
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print(f"Created: {'Yes' if user['created'] else 'No'}")
        
        elif choice == "4":
            users = generator.list_users()
            if users:
                print("\nExisting users:")
                for user in users:
                    status = "Active" if user['is_active'] else "Inactive"
                    print(f"- {user['username']} ({status}) - Created: {user['created_at']}")
            else:
                print("\nNo users found.")
        
        elif choice == "5":
            username = input("Enter username to delete: ").strip()
            if username:
                generator.delete_user(username)
            else:
                print("Username is required!")
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please enter 1-6.")

if __name__ == "__main__":
    main() 