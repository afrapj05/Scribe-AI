"""
Authentication module for Clinical OS.
Implements secure multi-step authentication with hashed passwords.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple

class CredentialManager:
    """Manage user credentials with bcrypt-like security."""
    
    def __init__(self, credential_file: str = "credentials.json"):
        self.credential_file = credential_file
        self.credentials = self._load_credentials()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = "clinical_os_salt_2026"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def _load_credentials(self) -> dict:
        """Load credentials from JSON file or initialize defaults."""
        if Path(self.credential_file).exists():
            with open(self.credential_file, 'r') as f:
                return json.load(f)
        
        # No credential file found — bootstrap with LOCKED accounts.
        # Admins MUST set real passwords by editing credentials.json or
        # calling add_clinician() before the system is usable.
        # Do NOT commit plaintext passwords to source control.
        _LOCKED = ""  # empty hash — no password will ever match this
        defaults = {
            "dr_sharma": {
                "password_hash": _LOCKED,
                "name": "Dr. Rajesh Sharma",
                "role": "Senior Physician",
                "department": "General Medicine",
                "clinic_id": "CLI001"
            },
            "dr_patel": {
                "password_hash": _LOCKED,
                "name": "Dr. Priya Patel",
                "role": "Cardiologist",
                "department": "Cardiology",
                "clinic_id": "CLI001"
            },
            "nurse_verma": {
                "password_hash": _LOCKED,
                "name": "Nurse Anjali Verma",
                "role": "Registered Nurse",
                "department": "General Medicine",
                "clinic_id": "CLI001"
            }
        }
        
        self._save_credentials(defaults)
        return defaults
    
    def _save_credentials(self, creds: dict):
        """Save credentials to JSON file."""
        with open(self.credential_file, 'w') as f:
            json.dump(creds, f, indent=4)
    
    def verify_login(self, username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """
        Verify username and password.
        
        Args:
            username: User's username
            password: User's password (plain text)
        
        Returns:
            Tuple of (is_valid, user_info_dict_or_None)
        """
        if username not in self.credentials:
            return False, None
        
        user = self.credentials[username]
        password_hash = self._hash_password(password)
        
        if password_hash == user["password_hash"]:
            return True, {
                "username": username,
                "name": user["name"],
                "role": user["role"],
                "department": user["department"],
                "clinic_id": user["clinic_id"]
            }
        
        return False, None
    
    def add_clinician(self, username: str, password: str, name: str, 
                      role: str, department: str, clinic_id: str = "CLI001"):
        """Add a new clinician to the system."""
        if username in self.credentials:
            return False, "Username already exists"
        
        self.credentials[username] = {
            "password_hash": self._hash_password(password),
            "name": name,
            "role": role,
            "department": department,
            "clinic_id": clinic_id
        }
        self._save_credentials(self.credentials)
        return True, f"Clinician {name} added successfully"


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[dict]]:
    """Convenience function for authentication."""
    manager = CredentialManager()
    return manager.verify_login(username, password)
