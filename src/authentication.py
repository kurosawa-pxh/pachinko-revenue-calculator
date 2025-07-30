"""
Authentication Manager for the Pachinko Revenue Calculator application.

Handles user authentication, password management, and security features.
"""

import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import hashlib
import secrets
import re
import logging
import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import bcrypt
import os
import json
from contextlib import contextmanager


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class AuthenticationManager:
    """
    Manages user authentication and security features for the Pachinko Revenue Calculator.

    Provides secure user registration, login, password management, and data encryption
    with protection against common security threats.
    """

    def __init__(self, db_path: str = "pachinko_auth.db", encryption_key: Optional[bytes] = None):
        """
        Initialize the Authentication Manager.

        Args:
            db_path: Path to the authentication database
            encryption_key: Optional encryption key for data encryption
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Initialize encryption
        if encryption_key:
            self.cipher_suite = Fernet(encryption_key)
        else:
            self.cipher_suite = self._generate_cipher_suite()

        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 8
        self.session_timeout = timedelta(hours=24)

        # Initialize database
        self._initialize_auth_database()

        # Initialize authenticator
        self._initialize_authenticator()

    def _generate_cipher_suite(self) -> Fernet:
        """Generate a new cipher suite for data encryption."""
        try:
            # Try to load existing key
            key_file = "encryption.key"
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                self.logger.info("Generated new encryption key")

            return Fernet(key)

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            # Fallback to session-only key
            return Fernet(Fernet.generate_key())

    def _initialize_auth_database(self) -> None:
        """Initialize the authentication database."""
        try:
            # Check if database is already initialized
            if self._is_auth_database_initialized():
                self.logger.info(
                    "Authentication database already initialized, skipping initialization")
                return

            self.logger.info("Initializing authentication database...")

            with self._get_auth_connection() as conn:
                # Create users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP,
                        password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        ip_address TEXT,
                        user_agent TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)

                # Create security logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        event_type TEXT NOT NULL,
                        event_description TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)

                # Create indexes
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_username ON users(username);")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_email ON users(email);")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token);")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id, timestamp);")

                conn.commit()
                self.logger.info(
                    "Authentication database initialized successfully")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize authentication database: {e}")
            # Don't raise exception to prevent app from crashing
            self.logger.warning(
                "Continuing with existing authentication database despite initialization error")

    def _is_auth_database_initialized(self) -> bool:
        """
        Check if the authentication database is already initialized.

        Returns:
            bool: True if database is initialized, False otherwise
        """
        try:
            with self._get_auth_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='users';
                """)
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.debug(
                f"Authentication database initialization check failed: {e}")
            return False

    @contextmanager
    def _get_auth_connection(self):
        """Context manager for authentication database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Authentication database error: {e}")
            raise AuthenticationError(f"Database connection failed: {e}")
        finally:
            if conn:
                conn.close()

    def _initialize_authenticator(self) -> None:
        """Initialize the streamlit-authenticator."""
        try:
            # Get user credentials from database
            credentials = self._get_user_credentials()

            if not credentials['usernames']:
                # Create default admin user if no users exist (skip in production deployment)
                if os.getenv('ENVIRONMENT', 'development') != 'production':
                    self._create_default_admin()
                    credentials = self._get_user_credentials()
                else:
                    # In production, use empty credentials to avoid password validation issues
                    credentials = {'usernames': {}, 'emails': {}, 'names': {}}

            # Initialize authenticator
            self.authenticator = stauth.Authenticate(
                credentials,
                'pachinko_auth_cookie',
                'pachinko_auth_key',
                cookie_expiry_days=1
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize authenticator: {e}")
            raise AuthenticationError(
                f"Authenticator initialization failed: {e}")

    def _get_user_credentials(self) -> Dict[str, Dict[str, Any]]:
        """Get user credentials in streamlit-authenticator format."""
        try:
            with self._get_auth_connection() as conn:
                cursor = conn.execute("""
                    SELECT username, email, password_hash, is_active 
                    FROM users 
                    WHERE is_active = TRUE
                """)
                users = cursor.fetchall()

                credentials = {
                    'usernames': {},
                    'emails': {},
                    'names': {}
                }

                for user in users:
                    username = user['username']
                    credentials['usernames'][username] = {
                        'email': user['email'],
                        'name': username.title(),
                        'password': user['password_hash']
                    }
                    credentials['emails'][user['email']] = username
                    credentials['names'][username.title()] = username

                return credentials

        except Exception as e:
            self.logger.error(f"Failed to get user credentials: {e}")
            return {'usernames': {}, 'emails': {}, 'names': {}}

    def _create_default_admin(self) -> None:
        """Create default admin user if no users exist."""
        try:
            # Check if any users already exist
            with self._get_auth_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users;")
                user_count = cursor.fetchone()[0]

                if user_count > 0:
                    self.logger.info(
                        "Users already exist, skipping default admin creation")
                    return

            default_username = "admin"
            default_email = "admin@pachinko.local"
            default_password = "admin123"  # Should be changed on first login

            self.register_user(
                default_username, default_email, default_password)
            self.logger.info("Default admin user created")

        except Exception as e:
            self.logger.error(f"Failed to create default admin: {e}")
            # Don't raise exception to prevent app from crashing

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength according to security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Length check
        if len(password) < self.password_min_length:
            errors.append(f"パスワードは{self.password_min_length}文字以上である必要があります")

        # Character variety checks
        if not re.search(r'[a-z]', password):
            errors.append("小文字を含む必要があります")

        if not re.search(r'[A-Z]', password):
            errors.append("大文字を含む必要があります")

        if not re.search(r'\d', password):
            errors.append("数字を含む必要があります")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("特殊文字を含む必要があります")

        # Common password checks
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]

        if password.lower() in common_passwords:
            errors.append("よく使われるパスワードは使用できません")

        return len(errors) == 0, errors

    def hash_password(self, password: str) -> Tuple[str, str]:
        """
        Hash a password with salt using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Tuple of (hashed_password, salt)
        """
        try:
            # Generate salt
            salt = bcrypt.gensalt()

            # Hash password
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

            return hashed.decode('utf-8'), salt.decode('utf-8')

        except Exception as e:
            self.logger.error(f"Password hashing failed: {e}")
            raise SecurityError(f"Password hashing failed: {e}")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password
            hashed_password: Hashed password from database

        Returns:
            bool: True if password matches
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False

    def register_user(self, username: str, email: str, password: str) -> bool:
        """
        Register a new user with validation and security checks.

        Args:
            username: Unique username
            email: User email address
            password: Plain text password

        Returns:
            bool: True if registration successful

        Raises:
            AuthenticationError: If registration fails
        """
        try:
            # Validate input
            if not username or not email or not password:
                raise AuthenticationError("すべてのフィールドは必須です")

            # Validate username format
            if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                raise AuthenticationError("ユーザー名は3-20文字の英数字とアンダースコアのみ使用可能です")

            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise AuthenticationError("有効なメールアドレスを入力してください")

            # Validate password strength
            is_valid, errors = self.validate_password_strength(password)
            if not is_valid:
                raise AuthenticationError("パスワード要件: " + ", ".join(errors))

            # Hash password
            hashed_password, salt = self.hash_password(password)

            # Save to database
            with self._get_auth_connection() as conn:
                # Check if username or email already exists
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE username = ? OR email = ?",
                    (username, email)
                )

                if cursor.fetchone()[0] > 0:
                    raise AuthenticationError("ユーザー名またはメールアドレスが既に使用されています")

                # Insert new user
                conn.execute("""
                    INSERT INTO users (username, email, password_hash, salt)
                    VALUES (?, ?, ?, ?)
                """, (username, email, hashed_password, salt))

                conn.commit()

                # Log security event
                self._log_security_event(
                    None, "USER_REGISTERED", f"New user registered: {username}")

                self.logger.info(f"User registered successfully: {username}")
                return True

        except AuthenticationError:
            raise
        except Exception as e:
            self.logger.error(f"User registration failed: {e}")
            raise AuthenticationError(f"ユーザー登録に失敗しました: {e}")

    def login_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Authenticate user login with security checks.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Tuple of (success, user_info)
        """
        try:
            with self._get_auth_connection() as conn:
                # Get user by username or email
                cursor = conn.execute("""
                    SELECT id, username, email, password_hash, is_active, 
                           failed_login_attempts, locked_until
                    FROM users 
                    WHERE (username = ? OR email = ?) AND is_active = TRUE
                """, (username, username))

                user = cursor.fetchone()

                if not user:
                    self._log_security_event(
                        None, "LOGIN_FAILED", f"Login attempt with invalid username: {username}")
                    raise AuthenticationError("ユーザー名またはパスワードが正しくありません")

                user_id = user['id']

                # Check if account is locked
                if user['locked_until']:
                    locked_until = datetime.fromisoformat(user['locked_until'])
                    if datetime.now() < locked_until:
                        remaining_time = locked_until - datetime.now()
                        minutes = int(remaining_time.total_seconds() / 60)
                        raise AuthenticationError(
                            f"アカウントがロックされています。{minutes}分後に再試行してください。")
                    else:
                        # Unlock account
                        conn.execute("""
                            UPDATE users 
                            SET failed_login_attempts = 0, locked_until = NULL 
                            WHERE id = ?
                        """, (user_id,))
                        conn.commit()

                # Verify password
                if not self.verify_password(password, user['password_hash']):
                    # Increment failed attempts
                    failed_attempts = user['failed_login_attempts'] + 1

                    # Check for suspicious activity before locking
                    is_suspicious, suspicious_reasons = self.detect_suspicious_activity(
                        user_id)

                    # Determine if account should be locked
                    should_lock = failed_attempts >= self.max_login_attempts or is_suspicious

                    if should_lock:
                        # Progressive lock duration based on suspicious activity
                        lock_duration = 30  # Default 30 minutes
                        if is_suspicious:
                            # Longer lock for suspicious activity
                            lock_duration = 120 if len(
                                suspicious_reasons) > 2 else 60

                        self.lock_account(
                            user_id,
                            f"Failed login attempts: {failed_attempts}, Suspicious: {', '.join(suspicious_reasons) if suspicious_reasons else 'None'}",
                            lock_duration
                        )

                        error_msg = "アカウントがロックされました。"
                        if suspicious_reasons:
                            error_msg += f" 検出された問題: {', '.join(suspicious_reasons)}"

                        raise AuthenticationError(error_msg)
                    else:
                        conn.execute("""
                            UPDATE users 
                            SET failed_login_attempts = ?
                            WHERE id = ?
                        """, (failed_attempts, user_id))

                    conn.commit()
                    self._log_security_event(
                        user_id, "LOGIN_FAILED", f"Failed login attempt #{failed_attempts}")
                    raise AuthenticationError("ユーザー名またはパスワードが正しくありません")

                # Successful login - check for suspicious activity even on success
                is_suspicious, suspicious_reasons = self.detect_suspicious_activity(
                    user_id)

                if is_suspicious and len(suspicious_reasons) > 1:
                    # Log suspicious successful login but don't block
                    self._log_security_event(
                        user_id, "SUSPICIOUS_LOGIN_SUCCESS",
                        f"Successful login with suspicious indicators: {', '.join(suspicious_reasons)}"
                    )

                    # Consider additional verification for highly suspicious logins
                    if len(suspicious_reasons) > 2:
                        self.logger.warning(
                            f"Highly suspicious login for user {user['username']}: {suspicious_reasons}")

                # Reset failed attempts
                conn.execute("""
                    UPDATE users 
                    SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), user_id))

                conn.commit()

                # Create session
                session_token = self._create_user_session(user_id)

                # Log successful login
                self._log_security_event(
                    user_id, "LOGIN_SUCCESS", f"Successful login")

                user_info = {
                    'id': user_id,
                    'username': user['username'],
                    'email': user['email'],
                    'session_token': session_token,
                    'suspicious_activity': is_suspicious,
                    'security_warnings': suspicious_reasons if is_suspicious else []
                }

                self.logger.info(
                    f"User logged in successfully: {user['username']}")
                return True, user_info

        except AuthenticationError:
            raise
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"ログインに失敗しました: {e}")

    def _create_user_session(self, user_id: int) -> str:
        """Create a new user session."""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + self.session_timeout

            with self._get_auth_connection() as conn:
                conn.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                """, (user_id, session_token, expires_at.isoformat()))

                conn.commit()

            return session_token

        except Exception as e:
            self.logger.error(f"Session creation failed: {e}")
            raise AuthenticationError(f"セッション作成に失敗しました: {e}")

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a user session token.

        Args:
            session_token: Session token to validate

        Returns:
            User info if session is valid, None otherwise
        """
        try:
            with self._get_auth_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.user_id, s.expires_at, u.username, u.email
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = ? AND s.is_active = TRUE
                """, (session_token,))

                session = cursor.fetchone()

                if not session:
                    return None

                # Check if session has expired
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    # Deactivate expired session
                    conn.execute("""
                        UPDATE user_sessions 
                        SET is_active = FALSE 
                        WHERE session_token = ?
                    """, (session_token,))
                    conn.commit()
                    return None

                return {
                    'id': session['user_id'],
                    'username': session['username'],
                    'email': session['email']
                }

        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return None

    def logout_user(self, session_token: str) -> bool:
        """
        Logout user by deactivating session.

        Args:
            session_token: Session token to deactivate

        Returns:
            bool: True if logout successful
        """
        try:
            with self._get_auth_connection() as conn:
                cursor = conn.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE session_token = ?
                """, (session_token,))

                conn.commit()

                if cursor.rowcount > 0:
                    self._log_security_event(
                        None, "LOGOUT", f"User logged out")
                    return True

                return False

        except Exception as e:
            self.logger.error(f"Logout failed: {e}")
            return False

    def _log_security_event(self, user_id: Optional[int], event_type: str,
                            description: str, ip_address: str = None,
                            user_agent: str = None) -> None:
        """Log security events for monitoring."""
        try:
            with self._get_auth_connection() as conn:
                conn.execute("""
                    INSERT INTO security_logs (user_id, event_type, event_description, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, event_type, description, ip_address, user_agent))

                conn.commit()

        except Exception as e:
            self.logger.error(f"Security logging failed: {e}")

    def detect_suspicious_activity(self, user_id: int, ip_address: str = None,
                                   user_agent: str = None) -> Tuple[bool, List[str]]:
        """
        Detect suspicious activity patterns for a user.

        Args:
            user_id: User ID to check
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Tuple of (is_suspicious, list_of_reasons)
        """
        try:
            suspicious_indicators = []

            with self._get_auth_connection() as conn:
                # Check for rapid login attempts (more than 10 in last hour)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE user_id = ? AND event_type IN ('LOGIN_FAILED', 'LOGIN_SUCCESS')
                    AND timestamp > datetime('now', '-1 hour')
                """, (user_id,))

                rapid_attempts = cursor.fetchone()[0]
                if rapid_attempts > 10:
                    suspicious_indicators.append("短時間での大量ログイン試行")

                # Check for multiple IP addresses in short time (last 2 hours)
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT ip_address) FROM security_logs 
                    WHERE user_id = ? AND ip_address IS NOT NULL
                    AND timestamp > datetime('now', '-2 hours')
                """, (user_id,))

                ip_count = cursor.fetchone()[0]
                if ip_count > 3:
                    suspicious_indicators.append("複数のIPアドレスからのアクセス")

                # Check for unusual user agent patterns
                if user_agent:
                    cursor = conn.execute("""
                        SELECT COUNT(DISTINCT user_agent) FROM security_logs 
                        WHERE user_id = ? AND user_agent IS NOT NULL
                        AND timestamp > datetime('now', '-24 hours')
                    """, (user_id,))

                    agent_count = cursor.fetchone()[0]
                    if agent_count > 5:
                        suspicious_indicators.append("複数のブラウザ/デバイスからのアクセス")

                # Check for failed login patterns (more than 3 failures in last 30 minutes)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE user_id = ? AND event_type = 'LOGIN_FAILED'
                    AND timestamp > datetime('now', '-30 minutes')
                """, (user_id,))

                recent_failures = cursor.fetchone()[0]
                if recent_failures > 3:
                    suspicious_indicators.append("短時間での複数回ログイン失敗")

                # Check for access outside normal hours (assuming 6 AM - 11 PM is normal)
                current_hour = datetime.now().hour
                if current_hour < 6 or current_hour > 23:
                    suspicious_indicators.append("通常時間外のアクセス")

                # Check for known malicious IP patterns (basic check)
                if ip_address:
                    # Check for localhost/private IP abuse
                    if ip_address.startswith(('127.', '10.', '192.168.', '172.')):
                        cursor = conn.execute("""
                            SELECT COUNT(*) FROM security_logs 
                            WHERE ip_address = ? AND event_type = 'LOGIN_FAILED'
                            AND timestamp > datetime('now', '-24 hours')
                        """, (ip_address,))

                        ip_failures = cursor.fetchone()[0]
                        if ip_failures > 20:
                            suspicious_indicators.append("同一IPからの大量失敗試行")

                # Log the suspicious activity check
                if suspicious_indicators:
                    self._log_security_event(
                        user_id, "SUSPICIOUS_ACTIVITY_DETECTED",
                        f"Detected: {', '.join(suspicious_indicators)}",
                        ip_address, user_agent
                    )

                return len(suspicious_indicators) > 0, suspicious_indicators

        except Exception as e:
            self.logger.error(f"Suspicious activity detection failed: {e}")
            return False, []

    def lock_account(self, user_id: int, reason: str = "Suspicious activity detected",
                     duration_minutes: int = None) -> bool:
        """
        Lock user account with progressive penalties.

        Args:
            user_id: User ID to lock
            reason: Reason for locking
            duration_minutes: Lock duration in minutes (auto-calculated if None)

        Returns:
            bool: True if account was locked successfully
        """
        try:
            with self._get_auth_connection() as conn:
                # Get current lock count for progressive penalties
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE user_id = ? AND event_type = 'ACCOUNT_LOCKED'
                    AND timestamp > datetime('now', '-7 days')
                """, (user_id,))

                recent_locks = cursor.fetchone()[0]

                # Progressive lock duration: 30min, 2hr, 8hr, 24hr, 7days
                if duration_minutes is None:
                    lock_durations = [30, 120, 480, 1440, 10080]  # minutes
                    duration_minutes = lock_durations[min(
                        recent_locks, len(lock_durations) - 1)]

                locked_until = datetime.now() + timedelta(minutes=duration_minutes)

                # Update user record
                cursor = conn.execute("""
                    UPDATE users 
                    SET locked_until = ?, failed_login_attempts = failed_login_attempts + 1
                    WHERE id = ?
                """, (locked_until.isoformat(), user_id))

                if cursor.rowcount == 0:
                    return False

                conn.commit()

                # Log the account lock
                self._log_security_event(
                    user_id, "ACCOUNT_LOCKED",
                    f"Account locked for {duration_minutes} minutes. Reason: {reason}"
                )

                self.logger.warning(
                    f"Account {user_id} locked for {duration_minutes} minutes: {reason}")
                return True

        except Exception as e:
            self.logger.error(f"Account locking failed: {e}")
            return False

    def unlock_account(self, user_id: int, admin_override: bool = False) -> bool:
        """
        Unlock user account.

        Args:
            user_id: User ID to unlock
            admin_override: Whether this is an admin override

        Returns:
            bool: True if account was unlocked successfully
        """
        try:
            with self._get_auth_connection() as conn:
                cursor = conn.execute("""
                    UPDATE users 
                    SET locked_until = NULL, failed_login_attempts = 0
                    WHERE id = ?
                """, (user_id,))

                if cursor.rowcount == 0:
                    return False

                conn.commit()

                # Log the unlock
                unlock_reason = "Admin override" if admin_override else "Automatic unlock"
                self._log_security_event(
                    user_id, "ACCOUNT_UNLOCKED", f"Account unlocked: {unlock_reason}"
                )

                self.logger.info(
                    f"Account {user_id} unlocked: {unlock_reason}")
                return True

        except Exception as e:
            self.logger.error(f"Account unlocking failed: {e}")
            return False

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.

        Args:
            data: Plain text data to encrypt

        Returns:
            str: Encrypted data as base64 string
        """
        try:
            if not data:
                return ""
            encrypted_data = self.cipher_suite.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            raise SecurityError(f"データの暗号化に失敗しました: {e}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            str: Decrypted plain text data
        """
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            raise SecurityError(f"データの復号化に失敗しました: {e}")

    def encrypt_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in user data dictionary.

        Args:
            data: Dictionary containing user data

        Returns:
            Dict: Dictionary with sensitive fields encrypted
        """
        try:
            encrypted_data = data.copy()

            # Fields that should be encrypted for privacy
            sensitive_fields = [
                'store_name', 'machine_name', 'user_notes',
                'location_details', 'personal_notes'
            ]

            for field in sensitive_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encrypt_data(
                        str(encrypted_data[field]))
                    encrypted_data[f"{field}_encrypted"] = True

            return encrypted_data

        except Exception as e:
            self.logger.error(f"User data encryption failed: {e}")
            raise SecurityError(f"ユーザーデータの暗号化に失敗しました: {e}")

    def decrypt_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in user data dictionary.

        Args:
            data: Dictionary containing encrypted user data

        Returns:
            Dict: Dictionary with sensitive fields decrypted
        """
        try:
            decrypted_data = data.copy()

            # Fields that should be decrypted
            sensitive_fields = [
                'store_name', 'machine_name', 'user_notes',
                'location_details', 'personal_notes'
            ]

            for field in sensitive_fields:
                if f"{field}_encrypted" in decrypted_data and decrypted_data.get(f"{field}_encrypted"):
                    if field in decrypted_data and decrypted_data[field]:
                        decrypted_data[field] = self.decrypt_data(
                            decrypted_data[field])
                    # Remove encryption flag
                    del decrypted_data[f"{field}_encrypted"]

            return decrypted_data

        except Exception as e:
            self.logger.error(f"User data decryption failed: {e}")
            raise SecurityError(f"ユーザーデータの復号化に失敗しました: {e}")

    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary for monitoring."""
        try:
            with self._get_auth_connection() as conn:
                # Get user count
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                active_users = cursor.fetchone()[0]

                # Get recent login attempts
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE event_type = 'LOGIN_FAILED' 
                    AND timestamp > datetime('now', '-24 hours')
                """)
                failed_logins_24h = cursor.fetchone()[0]

                # Get locked accounts
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE locked_until > datetime('now')
                """)
                locked_accounts = cursor.fetchone()[0]

                # Get active sessions
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM user_sessions 
                    WHERE is_active = TRUE AND expires_at > datetime('now')
                """)
                active_sessions = cursor.fetchone()[0]

                # Get suspicious activity count (last 24 hours)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE event_type IN ('SUSPICIOUS_ACTIVITY_DETECTED', 'SUSPICIOUS_LOGIN_SUCCESS')
                    AND timestamp > datetime('now', '-24 hours')
                """)
                suspicious_activities_24h = cursor.fetchone()[0]

                # Get unique IP addresses (last 24 hours)
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT ip_address) FROM security_logs 
                    WHERE ip_address IS NOT NULL
                    AND timestamp > datetime('now', '-24 hours')
                """)
                unique_ips_24h = cursor.fetchone()[0]

                # Get account locks in last 7 days
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM security_logs 
                    WHERE event_type = 'ACCOUNT_LOCKED'
                    AND timestamp > datetime('now', '-7 days')
                """)
                locks_7d = cursor.fetchone()[0]

                return {
                    'active_users': active_users,
                    'failed_logins_24h': failed_logins_24h,
                    'locked_accounts': locked_accounts,
                    'active_sessions': active_sessions,
                    'suspicious_activities_24h': suspicious_activities_24h,
                    'unique_ips_24h': unique_ips_24h,
                    'account_locks_7d': locks_7d,
                    'encryption_enabled': True,
                    'security_features': {
                        'data_encryption': True,
                        'suspicious_activity_detection': True,
                        'progressive_account_locking': True,
                        'session_management': True,
                        'security_logging': True
                    }
                }

        except Exception as e:
            self.logger.error(f"Security summary failed: {e}")
            return {
                'active_users': 0,
                'failed_logins_24h': 0,
                'locked_accounts': 0,
                'active_sessions': 0,
                'suspicious_activities_24h': 0,
                'unique_ips_24h': 0,
                'account_locks_7d': 0,
                'encryption_enabled': False,
                'security_features': {},
                'error': str(e)
            }

    def get_security_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get detailed security analytics for the specified period.

        Args:
            days: Number of days to analyze

        Returns:
            Dict containing security analytics data
        """
        try:
            with self._get_auth_connection() as conn:
                # Get daily login statistics
                cursor = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(CASE WHEN event_type = 'LOGIN_SUCCESS' THEN 1 END) as successful_logins,
                        COUNT(CASE WHEN event_type = 'LOGIN_FAILED' THEN 1 END) as failed_logins,
                        COUNT(CASE WHEN event_type = 'SUSPICIOUS_ACTIVITY_DETECTED' THEN 1 END) as suspicious_activities
                    FROM security_logs 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """.format(days))

                daily_stats = [dict(row) for row in cursor.fetchall()]

                # Get top suspicious activity reasons
                cursor = conn.execute("""
                    SELECT event_description, COUNT(*) as count
                    FROM security_logs 
                    WHERE event_type = 'SUSPICIOUS_ACTIVITY_DETECTED'
                    AND timestamp > datetime('now', '-{} days')
                    GROUP BY event_description
                    ORDER BY count DESC
                    LIMIT 10
                """.format(days))

                suspicious_reasons = [dict(row) for row in cursor.fetchall()]

                # Get IP address statistics
                cursor = conn.execute("""
                    SELECT 
                        ip_address,
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN event_type = 'LOGIN_FAILED' THEN 1 END) as failed_attempts,
                        COUNT(CASE WHEN event_type = 'LOGIN_SUCCESS' THEN 1 END) as successful_logins
                    FROM security_logs 
                    WHERE ip_address IS NOT NULL
                    AND timestamp > datetime('now', '-{} days')
                    GROUP BY ip_address
                    HAVING failed_attempts > 5 OR total_requests > 50
                    ORDER BY failed_attempts DESC, total_requests DESC
                    LIMIT 20
                """.format(days))

                ip_statistics = [dict(row) for row in cursor.fetchall()]

                # Get user activity patterns
                cursor = conn.execute("""
                    SELECT 
                        u.username,
                        COUNT(CASE WHEN s.event_type = 'LOGIN_SUCCESS' THEN 1 END) as successful_logins,
                        COUNT(CASE WHEN s.event_type = 'LOGIN_FAILED' THEN 1 END) as failed_logins,
                        COUNT(CASE WHEN s.event_type = 'ACCOUNT_LOCKED' THEN 1 END) as account_locks,
                        MAX(s.timestamp) as last_activity
                    FROM users u
                    LEFT JOIN security_logs s ON u.id = s.user_id
                    WHERE s.timestamp > datetime('now', '-{} days') OR s.timestamp IS NULL
                    GROUP BY u.id, u.username
                    ORDER BY failed_logins DESC, account_locks DESC
                """.format(days))

                user_patterns = [dict(row) for row in cursor.fetchall()]

                return {
                    'period_days': days,
                    'daily_statistics': daily_stats,
                    'suspicious_activity_reasons': suspicious_reasons,
                    'ip_address_statistics': ip_statistics,
                    'user_activity_patterns': user_patterns,
                    'generated_at': datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Security analytics failed: {e}")
            return {
                'period_days': days,
                'daily_statistics': [],
                'suspicious_activity_reasons': [],
                'ip_address_statistics': [],
                'user_activity_patterns': [],
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def render_login_form(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Render Streamlit login form.

        Returns:
            Tuple of (name, authentication_status, username)
        """
        try:
            # Refresh authenticator with current credentials
            self._initialize_authenticator()

            # Render login form
            name, authentication_status, username = self.authenticator.login(
                'ログイン', 'main')

            return name, authentication_status, username

        except Exception as e:
            self.logger.error(f"Login form rendering failed: {e}")
            st.error(f"ログインフォームの表示に失敗しました: {e}")
            return None, None, None

    def render_registration_form(self) -> bool:
        """
        Render user registration form.

        Returns:
            bool: True if registration was successful
        """
        try:
            st.markdown("### 🔐 新規ユーザー登録")

            with st.form("registration_form"):
                username = st.text_input("ユーザー名", help="3-20文字の英数字とアンダースコア")
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                password_confirm = st.text_input("パスワード確認", type="password")

                submitted = st.form_submit_button("登録")

                if submitted:
                    if password != password_confirm:
                        st.error("パスワードが一致しません")
                        return False

                    try:
                        success = self.register_user(username, email, password)
                        if success:
                            st.success("✅ ユーザー登録が完了しました！ログインしてください。")
                            return True
                    except AuthenticationError as e:
                        st.error(f"❌ 登録エラー: {e}")
                    except Exception as e:
                        st.error(f"❌ 予期しないエラーが発生しました: {e}")

            return False

        except Exception as e:
            self.logger.error(f"Registration form rendering failed: {e}")
            st.error(f"登録フォームの表示に失敗しました: {e}")
            return False

    def render_security_dashboard(self) -> None:
        """
        Render security monitoring dashboard for administrators.
        """
        try:
            st.markdown("### 🔒 セキュリティダッシュボード")

            # Get security summary
            summary = self.get_security_summary()

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("アクティブユーザー", summary['active_users'])

            with col2:
                st.metric("24時間以内の失敗ログイン", summary['failed_logins_24h'])

            with col3:
                st.metric("ロック中のアカウント", summary['locked_accounts'])

            with col4:
                st.metric("アクティブセッション", summary['active_sessions'])

            # Additional security metrics
            col5, col6, col7 = st.columns(3)

            with col5:
                st.metric("疑わしい活動 (24h)", summary.get(
                    'suspicious_activities_24h', 0))

            with col6:
                st.metric("ユニークIP (24h)", summary.get('unique_ips_24h', 0))

            with col7:
                st.metric("アカウントロック (7d)", summary.get('account_locks_7d', 0))

            # Security features status
            st.markdown("#### セキュリティ機能状態")
            features = summary.get('security_features', {})

            feature_cols = st.columns(3)
            feature_names = {
                'data_encryption': 'データ暗号化',
                'suspicious_activity_detection': '不審な活動検出',
                'progressive_account_locking': '段階的アカウントロック',
                'session_management': 'セッション管理',
                'security_logging': 'セキュリティログ'
            }

            for i, (key, name) in enumerate(feature_names.items()):
                with feature_cols[i % 3]:
                    status = "✅ 有効" if features.get(key, False) else "❌ 無効"
                    st.write(f"**{name}**: {status}")

            # Detailed analytics
            if st.expander("詳細分析", expanded=False):
                analytics_days = st.selectbox(
                    "分析期間", [1, 3, 7, 14, 30], index=2)
                analytics = self.get_security_analytics(analytics_days)

                if analytics['daily_statistics']:
                    st.markdown("##### 日別統計")
                    st.dataframe(analytics['daily_statistics'])

                if analytics['suspicious_activity_reasons']:
                    st.markdown("##### 疑わしい活動の理由")
                    st.dataframe(analytics['suspicious_activity_reasons'])

                if analytics['ip_address_statistics']:
                    st.markdown("##### IPアドレス統計 (高リスク)")
                    st.dataframe(analytics['ip_address_statistics'])

            # Manual account management
            if st.expander("アカウント管理", expanded=False):
                st.markdown("##### アカウントロック解除")

                with st.form("unlock_account_form"):
                    username_to_unlock = st.text_input("ユーザー名")
                    admin_override = st.checkbox("管理者権限で強制解除")

                    if st.form_submit_button("アカウント解除"):
                        if username_to_unlock:
                            # Get user ID from username
                            with self._get_auth_connection() as conn:
                                cursor = conn.execute(
                                    "SELECT id FROM users WHERE username = ?",
                                    (username_to_unlock,)
                                )
                                user_row = cursor.fetchone()

                                if user_row:
                                    success = self.unlock_account(
                                        user_row['id'], admin_override)
                                    if success:
                                        st.success(
                                            f"✅ アカウント '{username_to_unlock}' のロックを解除しました")
                                    else:
                                        st.error("❌ アカウントロック解除に失敗しました")
                                else:
                                    st.error("❌ ユーザーが見つかりません")
                        else:
                            st.error("❌ ユーザー名を入力してください")

        except Exception as e:
            self.logger.error(f"Security dashboard rendering failed: {e}")
            st.error(f"セキュリティダッシュボードの表示に失敗しました: {e}")

    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of encrypted data and security logs.

        Returns:
            Dict containing validation results
        """
        try:
            validation_results = {
                'encryption_test_passed': False,
                'database_integrity_ok': False,
                'security_logs_consistent': False,
                'issues_found': []
            }

            # Test encryption/decryption functionality
            try:
                test_data = "テストデータ123"
                encrypted = self.encrypt_data(test_data)
                decrypted = self.decrypt_data(encrypted)

                if decrypted == test_data:
                    validation_results['encryption_test_passed'] = True
                else:
                    validation_results['issues_found'].append(
                        "暗号化/復号化テストが失敗しました")
            except Exception as e:
                validation_results['issues_found'].append(f"暗号化テストエラー: {e}")

            # Check database integrity
            try:
                with self._get_auth_connection() as conn:
                    # Check for orphaned sessions
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM user_sessions s
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE u.id IS NULL
                    """)
                    orphaned_sessions = cursor.fetchone()[0]

                    if orphaned_sessions > 0:
                        validation_results['issues_found'].append(
                            f"孤立したセッション: {orphaned_sessions}件")

                    # Check for inconsistent security logs
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM security_logs s
                        LEFT JOIN users u ON s.user_id = u.id
                        WHERE s.user_id IS NOT NULL AND u.id IS NULL
                    """)
                    orphaned_logs = cursor.fetchone()[0]

                    if orphaned_logs > 0:
                        validation_results['issues_found'].append(
                            f"孤立したセキュリティログ: {orphaned_logs}件")

                    if orphaned_sessions == 0 and orphaned_logs == 0:
                        validation_results['database_integrity_ok'] = True

            except Exception as e:
                validation_results['issues_found'].append(
                    f"データベース整合性チェックエラー: {e}")

            # Check security logs consistency
            try:
                with self._get_auth_connection() as conn:
                    # Check for users with successful logins but no user record
                    cursor = conn.execute("""
                        SELECT COUNT(DISTINCT user_id) FROM security_logs 
                        WHERE event_type = 'LOGIN_SUCCESS' 
                        AND user_id NOT IN (SELECT id FROM users)
                    """)
                    inconsistent_logs = cursor.fetchone()[0]

                    if inconsistent_logs == 0:
                        validation_results['security_logs_consistent'] = True
                    else:
                        validation_results['issues_found'].append(
                            f"不整合なセキュリティログ: {inconsistent_logs}件")

            except Exception as e:
                validation_results['issues_found'].append(
                    f"セキュリティログ整合性チェックエラー: {e}")

            validation_results['overall_status'] = (
                validation_results['encryption_test_passed'] and
                validation_results['database_integrity_ok'] and
                validation_results['security_logs_consistent']
            )

            return validation_results

        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return {
                'encryption_test_passed': False,
                'database_integrity_ok': False,
                'security_logs_consistent': False,
                'overall_status': False,
                'issues_found': [f"検証プロセスエラー: {e}"]
            }
