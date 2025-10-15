"""
Auth Manager - Lightweight authentication system for TodoDB

Uses:
- SQLite for user storage (free, local)
- JWT for token-based auth (stateless)
- bcrypt for password hashing (secure)

Features:
- Multi-user support with roles
- Token-based authentication
- No external services required
"""

import sqlite3
import jwt
import bcrypt
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    """User roles with different permissions"""
    ADMIN = "admin"  # Full access: create/edit/delete all tasks
    DEVELOPER = "developer"  # Can create/edit own tasks, view all
    VIEWER = "viewer"  # Read-only access


@dataclass
class User:
    """User model"""
    id: int
    username: str
    role: UserRole
    created_at: str
    last_login: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role.value,
            'created_at': self.created_at,
            'last_login': self.last_login
        }


class AuthManager:
    """Lightweight authentication manager"""

    def __init__(
        self,
        db_path: str = "cortex/data/auth.db",
        jwt_secret: Optional[str] = None
    ):
        """
        Initialize Auth Manager

        Args:
            db_path: Path to SQLite database
            jwt_secret: Secret key for JWT (auto-generated if None)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # JWT secret (persistent across sessions)
        self.jwt_secret_file = self.db_path.parent / ".jwt_secret"
        self.jwt_secret = self._load_or_generate_secret(jwt_secret)

        # Initialize database
        self._init_db()

    def _load_or_generate_secret(self, provided_secret: Optional[str]) -> str:
        """Load existing JWT secret or generate new one"""
        if provided_secret:
            return provided_secret

        # Try to load existing secret
        if self.jwt_secret_file.exists():
            try:
                return self.jwt_secret_file.read_text().strip()
            except Exception:
                pass

        # Generate new secret
        secret = secrets.token_urlsafe(32)
        try:
            self.jwt_secret_file.write_text(secret)
            self.jwt_secret_file.chmod(0o600)  # Read/write for owner only
        except Exception as e:
            print(f"Warning: Could not save JWT secret: {e}")

        return secret

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Create default admin if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                self._create_default_admin(cursor)

            conn.commit()

    def _create_default_admin(self, cursor):
        """Create default admin user (Cortex/cortex123)"""
        username = "Cortex"
        password = "cortex123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO users (username, password_hash, role, created_at, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (username, password_hash, UserRole.ADMIN.value, datetime.now().isoformat()))

        print(f"✓ Default admin user created: {username} / {password}")
        print(f"  Change password after first login!")

    def register_user(
        self,
        username: str,
        password: str,
        role: UserRole = UserRole.DEVELOPER
    ) -> Dict[str, Any]:
        """
        Register a new user

        Args:
            username: Username (must be unique)
            password: Plain password (will be hashed)
            role: User role

        Returns:
            Dict with success status and message
        """
        if len(password) < 6:
            return {
                'success': False,
                'error': 'Password must be at least 6 characters'
            }

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, created_at, is_active)
                    VALUES (?, ?, ?, ?, 1)
                """, (username, password_hash, role.value, datetime.now().isoformat()))
                conn.commit()

                return {
                    'success': True,
                    'message': f'User {username} registered successfully',
                    'user_id': cursor.lastrowid
                }

        except sqlite3.IntegrityError:
            return {
                'success': False,
                'error': f'Username {username} already exists'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and generate JWT token

        Args:
            username: Username
            password: Plain password

        Returns:
            Dict with token and user info if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, role, created_at, is_active
                FROM users
                WHERE username = ?
            """, (username,))

            row = cursor.fetchone()

            if not row:
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }

            user_id, username, password_hash, role, created_at, is_active = row

            if not is_active:
                return {
                    'success': False,
                    'error': 'User account is disabled'
                }

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }

            # Update last login
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), user_id))
            conn.commit()

            # Generate JWT token (expires in 7 days)
            token_payload = {
                'user_id': user_id,
                'username': username,
                'role': role,
                'exp': datetime.utcnow() + timedelta(days=7)
            }
            token = jwt.encode(token_payload, self.jwt_secret, algorithm='HS256')

            user = User(
                id=user_id,
                username=username,
                role=UserRole(role),
                created_at=created_at,
                last_login=datetime.now().isoformat()
            )

            return {
                'success': True,
                'token': token,
                'user': user.to_dict(),
                'expires_in': '7 days'
            }

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and return user info

        Args:
            token: JWT token

        Returns:
            Dict with user info if valid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])

            # Check if user still exists and is active
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, role, is_active
                    FROM users
                    WHERE id = ?
                """, (payload['user_id'],))

                row = cursor.fetchone()

                if not row or not row[3]:  # Not found or not active
                    return {
                        'success': False,
                        'error': 'Invalid or expired token'
                    }

                return {
                    'success': True,
                    'user_id': row[0],
                    'username': row[1],
                    'role': row[2]
                }

        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'error': 'Token has expired'
            }
        except jwt.InvalidTokenError:
            return {
                'success': False,
                'error': 'Invalid token'
            }

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, created_at, last_login
                FROM users
                WHERE id = ? AND is_active = 1
            """, (user_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return User(
                id=row[0],
                username=row[1],
                role=UserRole(row[2]),
                created_at=row[3],
                last_login=row[4]
            )

    def list_users(self) -> list:
        """List all active users"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, created_at, last_login
                FROM users
                WHERE is_active = 1
                ORDER BY created_at DESC
            """)

            users = []
            for row in cursor.fetchall():
                users.append(User(
                    id=row[0],
                    username=row[1],
                    role=UserRole(row[2]),
                    created_at=row[3],
                    last_login=row[4]
                ))

            return users

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Change user password"""
        if len(new_password) < 6:
            return {
                'success': False,
                'error': 'New password must be at least 6 characters'
            }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT password_hash FROM users WHERE id = ?
            """, (user_id,))

            row = cursor.fetchone()

            if not row:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            # Verify old password
            if not bcrypt.checkpw(old_password.encode('utf-8'), row[0]):
                return {
                    'success': False,
                    'error': 'Invalid old password'
                }

            # Hash new password
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            cursor.execute("""
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            """, (new_hash, user_id))
            conn.commit()

            return {
                'success': True,
                'message': 'Password changed successfully'
            }


def create_auth_manager(db_path: str = "cortex/data/auth.db") -> AuthManager:
    """Factory function to create AuthManager"""
    return AuthManager(db_path)


# Test if run directly
if __name__ == "__main__":
    print("Testing Auth Manager...")

    auth = AuthManager("cortex/data/test_auth.db")

    # Test 1: Login with default admin
    print("\n1. Testing default admin login...")
    result = auth.login("Cortex", "cortex123")
    if result['success']:
        print(f"✓ Login successful!")
        print(f"  Token: {result['token'][:50]}...")
        print(f"  User: {result['user']['username']} ({result['user']['role']})")
        token = result['token']
    else:
        print(f"✗ Login failed: {result['error']}")

    # Test 2: Verify token
    print("\n2. Testing token verification...")
    verify_result = auth.verify_token(token)
    if verify_result['success']:
        print(f"✓ Token valid!")
        print(f"  User: {verify_result['username']}")
    else:
        print(f"✗ Token invalid: {verify_result['error']}")

    # Test 3: Register new user
    print("\n3. Testing user registration...")
    reg_result = auth.register_user("developer1", "dev123", UserRole.DEVELOPER)
    if reg_result['success']:
        print(f"✓ {reg_result['message']}")
    else:
        print(f"✗ Registration failed: {reg_result['error']}")

    # Test 4: List users
    print("\n4. Listing all users...")
    users = auth.list_users()
    for user in users:
        print(f"  - {user.username} ({user.role.value})")

    print("\n✓ Auth Manager works correctly!")
