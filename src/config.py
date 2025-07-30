"""
Configuration management for the Pachinko Revenue Calculator application.

Handles environment variables, database connections, and deployment settings
for both development and production environments.
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class Config:
    """
    Configuration manager for the application.

    Manages environment variables, database connections, and deployment settings
    with support for both SQLite (development) and PostgreSQL (production).
    """

    def __init__(self):
        """Initialize configuration manager."""
        self.logger = logging.getLogger(__name__)
        self._config = self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Dictionary containing all configuration settings
        """
        # Environment detection
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment == 'production'

        # Database configuration
        database_config = self._get_database_config(is_production)

        # Application configuration
        config = {
            'environment': environment,
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'database': database_config,
            'security': self._get_security_config(),
            'ui': self._get_ui_config(),
            'features': self._get_features_config(),
            'deployment': self._get_deployment_config(is_production),
            'logging': self._get_logging_config()
        }

        return config

    def _get_database_config(self, is_production: bool) -> Dict[str, Any]:
        """
        Get database configuration based on environment.

        Args:
            is_production: Whether running in production environment

        Returns:
            Database configuration dictionary
        """
        if is_production:
            # Production: Use Supabase PostgreSQL
            database_url = os.getenv('DATABASE_URL') or os.getenv(
                'SUPABASE_DATABASE_URL')

            if not database_url:
                raise ConfigurationError(
                    "DATABASE_URL or SUPABASE_DATABASE_URL must be set in production"
                )

            # Parse the database URL
            parsed = urlparse(database_url)

            return {
                'type': 'postgresql',
                'url': database_url,
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/') if parsed.path else None,
                'username': parsed.username,
                'password': parsed.password,
                'ssl_mode': os.getenv('DB_SSL_MODE', 'require'),
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
                'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
                'enable_encryption': os.getenv('ENABLE_DB_ENCRYPTION', 'true').lower() == 'true'
            }
        else:
            # Development: Use SQLite
            return {
                'type': 'sqlite',
                'path': os.getenv('DATABASE_PATH', 'pachinko_data.db'),
                'auth_path': os.getenv('AUTH_DATABASE_PATH', 'pachinko_auth.db'),
                'enable_encryption': os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true'
            }

    def _get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600')),
            'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            'enable_2fa': os.getenv('ENABLE_2FA', 'false').lower() == 'true',
            'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
            'jwt_expiration': int(os.getenv('JWT_EXPIRATION', '86400')),
            'encryption_key': os.getenv('ENCRYPTION_KEY'),
            'hash_rounds': int(os.getenv('HASH_ROUNDS', '12'))
        }

    def _get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return {
            'theme': os.getenv('UI_THEME', 'flashy'),
            'enable_animations': os.getenv('ENABLE_ANIMATIONS', 'true').lower() == 'true',
            'mobile_optimized': os.getenv('MOBILE_OPTIMIZED', 'true').lower() == 'true',
            'page_title': os.getenv('PAGE_TITLE', '勝てるクン - パチンコ収支管理'),
            'page_icon': os.getenv('PAGE_ICON', '🎰'),
            'layout': os.getenv('LAYOUT', 'wide'),
            'sidebar_state': os.getenv('SIDEBAR_STATE', 'expanded')
        }

    def _get_features_config(self) -> Dict[str, Any]:
        """Get features configuration."""
        return {
            'offline_mode': os.getenv('ENABLE_OFFLINE', 'true').lower() == 'true',
            'export_enabled': os.getenv('ENABLE_EXPORT', 'true').lower() == 'true',
            'advanced_stats': os.getenv('ENABLE_ADVANCED_STATS', 'true').lower() == 'true',
            'data_backup': os.getenv('ENABLE_DATA_BACKUP', 'false').lower() == 'true',
            'analytics': os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true',
            'notifications': os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
        }

    def _get_deployment_config(self, is_production: bool) -> Dict[str, Any]:
        """Get deployment configuration."""
        return {
            'platform': os.getenv('DEPLOYMENT_PLATFORM', 'streamlit_cloud'),
            'cdn_url': os.getenv('CDN_URL'),
            'static_url': os.getenv('STATIC_URL', '/static'),
            # 10MB
            'max_upload_size': int(os.getenv('MAX_UPLOAD_SIZE', '10485760')),
            'rate_limit': int(os.getenv('RATE_LIMIT', '100')),
            'enable_caching': os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            'cache_ttl': int(os.getenv('CACHE_TTL', '300')),
            'health_check_enabled': os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
            'metrics_enabled': os.getenv('METRICS_ENABLED', 'false').lower() == 'true',
            'free_tier_limits': {
                'max_users': int(os.getenv('MAX_USERS', '100')),
                'max_sessions_per_user': int(os.getenv('MAX_SESSIONS_PER_USER', '1000')),
                'max_db_size_mb': int(os.getenv('MAX_DB_SIZE_MB', '50')),
                'max_bandwidth_mb': int(os.getenv('MAX_BANDWIDTH_MB', '2048'))
            }
        }

    def _get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO').upper(),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file_enabled': os.getenv('LOG_TO_FILE', 'false').lower() == 'true',
            'file_path': os.getenv('LOG_FILE_PATH', 'app.log'),
            # 10MB
            'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', '10485760')),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'console_enabled': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
        }

    def _validate_configuration(self) -> None:
        """
        Validate the loaded configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        config = self._config

        # Validate database configuration
        if config['database']['type'] == 'postgresql':
            required_fields = ['url', 'host',
                               'database', 'username', 'password']
            for field in required_fields:
                if not config['database'].get(field):
                    raise ConfigurationError(
                        f"Database {field} is required for PostgreSQL")

        # Validate security configuration
        if config['environment'] == 'production':
            if config['security']['secret_key'] == 'dev-secret-key-change-in-production':
                raise ConfigurationError(
                    "SECRET_KEY must be set in production")

            if not config['security']['encryption_key']:
                self.logger.warning(
                    "ENCRYPTION_KEY not set - data encryption will be disabled")

        # Validate free tier limits
        limits = config['deployment']['free_tier_limits']
        if limits['max_db_size_mb'] > 500:  # Supabase free tier limit
            self.logger.warning(
                "Database size limit exceeds Supabase free tier (500MB)")

        if limits['max_bandwidth_mb'] > 2048:  # Supabase free tier limit
            self.logger.warning(
                "Bandwidth limit exceeds Supabase free tier (2GB)")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'database.type')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config['database']

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self._config['security']

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self._config['environment'] == 'production'

    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config['debug']

    def get_database_url(self) -> Optional[str]:
        """Get database URL for PostgreSQL connections."""
        if self._config['database']['type'] == 'postgresql':
            return self._config['database']['url']
        return None

    def get_free_tier_limits(self) -> Dict[str, int]:
        """Get free tier limits configuration."""
        return self._config['deployment']['free_tier_limits']

    def check_free_tier_compliance(self, current_usage: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check if current usage complies with free tier limits.

        Args:
            current_usage: Dictionary with current usage metrics

        Returns:
            Dictionary with compliance status for each limit
        """
        limits = self.get_free_tier_limits()

        return {
            'users': current_usage.get('users', 0) <= limits['max_users'],
            'sessions_per_user': current_usage.get('max_sessions_per_user', 0) <= limits['max_sessions_per_user'],
            'db_size': current_usage.get('db_size_mb', 0) <= limits['max_db_size_mb'],
            'bandwidth': current_usage.get('bandwidth_mb', 0) <= limits['max_bandwidth_mb']
        }

    def get_connection_string(self) -> str:
        """
        Get database connection string.

        Returns:
            Database connection string
        """
        db_config = self._config['database']

        if db_config['type'] == 'postgresql':
            return db_config['url']
        else:
            return db_config['path']

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_config = self._config['logging']

        # Configure logging level
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format']
        )

        # Add file handler if enabled
        if log_config['file_enabled']:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                log_config['file_path'],
                maxBytes=log_config['max_file_size'],
                backupCount=log_config['backup_count']
            )
            file_handler.setFormatter(logging.Formatter(log_config['format']))

            # Add to root logger
            logging.getLogger().addHandler(file_handler)

    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary (sensitive values masked)
        """
        config_copy = self._config.copy()

        # Mask sensitive values
        if 'security' in config_copy:
            security = config_copy['security'].copy()
            security['secret_key'] = '***MASKED***'
            security['encryption_key'] = '***MASKED***' if security.get(
                'encryption_key') else None
            config_copy['security'] = security

        if 'database' in config_copy and config_copy['database']['type'] == 'postgresql':
            db = config_copy['database'].copy()
            db['password'] = '***MASKED***'
            db['url'] = '***MASKED***'
            config_copy['database'] = db

        return config_copy


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config()

    return _config_instance


def reload_config() -> Config:
    """
    Reload configuration from environment variables.

    Returns:
        New Config instance
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance
