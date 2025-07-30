"""
Main application class for the Pachinko Revenue Calculator.

Integrates all components and manages the overall application lifecycle.
"""

import streamlit as st
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

from .database import DatabaseManager, DatabaseError
from .ui_manager import UIManager
from .stats import StatsCalculator
from .authentication import AuthenticationManager, AuthenticationError
from .offline import OfflineStorageManager
from .export import ExportManager
from .deployment import get_deployment_manager
from .error_handler import handle_error, ErrorCategory, ErrorSeverity


class PachinkoApp:
    """
    Main application class that integrates all components of the Pachinko Revenue Calculator.

    This class serves as the central coordinator for all application components,
    managing initialization, configuration, and the overall application lifecycle.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Pachinko application with all components.

        Args:
            config: Optional configuration dictionary for customizing app behavior
        """
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()

        # Initialize core components
        self.db_manager: Optional[DatabaseManager] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.stats_calculator: Optional[StatsCalculator] = None
        self.ui_manager: Optional[UIManager] = None
        self.offline_manager: Optional[OfflineStorageManager] = None
        self.export_manager: Optional[ExportManager] = None
        self.deployment_manager = get_deployment_manager()

        # Application state
        self.is_initialized = False
        self.current_user = None

        # Initialize components
        self._initialize_components()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for the application.

        Returns:
            Default configuration dictionary
        """
        return {
            'database': {
                'path': os.getenv('DATABASE_PATH', 'pachinko_data.db'),
                'auth_path': os.getenv('AUTH_DATABASE_PATH', 'pachinko_auth.db'),
                'enable_encryption': os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true'
            },
            'ui': {
                'theme': 'flashy',
                'enable_animations': True,
                'mobile_optimized': True
            },
            'features': {
                'offline_mode': True,
                'export_enabled': True,
                'advanced_stats': True
            },
            'security': {
                'session_timeout': 3600,  # 1 hour
                'max_login_attempts': 5,
                'password_min_length': 8
            },
            'deployment': {
                'environment': os.getenv('ENVIRONMENT', 'development'),
                'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """
        Setup logging configuration for the application.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('pachinko_app')

        if not logger.handlers:
            # Configure logging level based on environment
            level = logging.DEBUG if self.config['deployment']['debug_mode'] else logging.INFO
            logger.setLevel(level)

            # Create console handler
            handler = logging.StreamHandler()
            handler.setLevel(level)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)

            logger.addHandler(handler)

        return logger

    def _initialize_components(self) -> None:
        """
        Initialize all application components in the correct order.
        """
        try:
            self.logger.info(
                "Initializing Pachinko Revenue Calculator components...")

            # Initialize authentication manager first
            self._initialize_auth_manager()

            # Initialize database manager with encryption if enabled
            self._initialize_database_manager()

            # Initialize statistics calculator
            self._initialize_stats_calculator()

            # Initialize offline storage manager
            self._initialize_offline_manager()

            # Initialize export manager
            self._initialize_export_manager()

            # Initialize UI manager last (depends on other components)
            self._initialize_ui_manager()

            self.is_initialized = True
            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            handle_error(e, ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL)
            raise

    def _initialize_auth_manager(self) -> None:
        """Initialize the authentication manager."""
        try:
            auth_config = self.config['database']
            security_config = self.config['security']

            self.auth_manager = AuthenticationManager(
                db_path=auth_config['auth_path'],
                encryption_key=None  # Will be generated internally
            )

            # Configure security settings
            self.auth_manager.session_timeout = security_config['session_timeout']
            self.auth_manager.max_login_attempts = security_config['max_login_attempts']
            self.auth_manager.password_min_length = security_config['password_min_length']

            self.logger.info("Authentication manager initialized")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize authentication manager: {e}")
            raise

    def _initialize_database_manager(self) -> None:
        """Initialize the database manager with optional encryption."""
        try:
            db_config = self.config['database']

            # Pass encryption manager if encryption is enabled
            encryption_manager = self.auth_manager if db_config['enable_encryption'] else None

            self.db_manager = DatabaseManager(
                db_path=db_config['path'],
                encryption_manager=encryption_manager
            )

            self.logger.info("Database manager initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {e}")
            raise

    def _initialize_stats_calculator(self) -> None:
        """Initialize the statistics calculator."""
        try:
            self.stats_calculator = StatsCalculator(self.db_manager)
            self.logger.info("Statistics calculator initialized")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize statistics calculator: {e}")
            raise

    def _initialize_offline_manager(self) -> None:
        """Initialize the offline storage manager."""
        try:
            if self.config['features']['offline_mode']:
                self.offline_manager = OfflineStorageManager()
                self.logger.info("Offline storage manager initialized")
            else:
                self.logger.info("Offline mode disabled")

        except Exception as e:
            self.logger.error(f"Failed to initialize offline manager: {e}")
            # Don't raise - offline functionality is optional

    def _initialize_export_manager(self) -> None:
        """Initialize the export manager."""
        try:
            if self.config['features']['export_enabled']:
                self.export_manager = ExportManager(self.stats_calculator)
                self.logger.info("Export manager initialized")
            else:
                self.logger.info("Export functionality disabled")

        except Exception as e:
            self.logger.error(f"Failed to initialize export manager: {e}")
            # Don't raise - export functionality is optional

    def _initialize_ui_manager(self) -> None:
        """Initialize the UI manager."""
        try:
            self.ui_manager = UIManager(
                db_manager=self.db_manager,
                stats_calculator=self.stats_calculator
            )

            # Configure UI manager with additional components
            if self.export_manager:
                self.ui_manager.export_manager = self.export_manager

            if self.offline_manager:
                self.ui_manager.offline_manager = self.offline_manager

            self.ui_manager.auth_manager = self.auth_manager

            self.logger.info("UI manager initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize UI manager: {e}")
            raise

    def get_database_manager(self) -> DatabaseManager:
        """
        Get the database manager instance.

        Returns:
            DatabaseManager instance

        Raises:
            RuntimeError: If the app is not initialized
        """
        if not self.is_initialized or not self.db_manager:
            raise RuntimeError("Application not properly initialized")
        return self.db_manager

    def get_ui_manager(self) -> UIManager:
        """
        Get the UI manager instance.

        Returns:
            UIManager instance

        Raises:
            RuntimeError: If the app is not initialized
        """
        if not self.is_initialized or not self.ui_manager:
            raise RuntimeError("Application not properly initialized")
        return self.ui_manager

    def get_stats_calculator(self) -> StatsCalculator:
        """
        Get the statistics calculator instance.

        Returns:
            StatsCalculator instance

        Raises:
            RuntimeError: If the app is not initialized
        """
        if not self.is_initialized or not self.stats_calculator:
            raise RuntimeError("Application not properly initialized")
        return self.stats_calculator

    def get_auth_manager(self) -> AuthenticationManager:
        """
        Get the authentication manager instance.

        Returns:
            AuthenticationManager instance

        Raises:
            RuntimeError: If the app is not initialized
        """
        if not self.is_initialized or not self.auth_manager:
            raise RuntimeError("Application not properly initialized")
        return self.auth_manager

    def get_offline_manager(self) -> Optional[OfflineStorageManager]:
        """
        Get the offline storage manager instance.

        Returns:
            OfflineStorageManager instance or None if disabled
        """
        return self.offline_manager

    def get_export_manager(self) -> Optional[ExportManager]:
        """
        Get the export manager instance.

        Returns:
            ExportManager instance or None if disabled
        """
        return self.export_manager

    def get_deployment_manager(self):
        """
        Get the deployment manager instance.

        Returns:
            DeploymentManager instance
        """
        return self.deployment_manager

    def check_free_tier_limits(self) -> bool:
        """
        Check if the application is within free tier limits.

        Returns:
            True if within limits, False otherwise
        """
        try:
            allowed, error_message = self.deployment_manager.enforce_free_tier_limits()
            if not allowed and error_message:
                st.error(f"🚫 {error_message}")
                st.info("無料枠の制限に達しました。しばらく時間をおいてから再度お試しください。")
            return allowed
        except Exception as e:
            self.logger.error(f"Failed to check free tier limits: {e}")
            return True  # Allow operation if check fails

    def is_ready(self) -> bool:
        """
        Check if the application is ready to run.

        Returns:
            True if all required components are initialized
        """
        return (
            self.is_initialized and
            self.db_manager is not None and
            self.ui_manager is not None and
            self.stats_calculator is not None and
            self.auth_manager is not None
        )

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of all components.

        Returns:
            Dictionary containing health status of each component
        """
        status = {
            'app_initialized': self.is_initialized,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # Check database manager
        try:
            if self.db_manager:
                # Try a simple database operation
                self.db_manager.get_sessions("health_check", limit=1)
                status['components']['database'] = 'healthy'
            else:
                status['components']['database'] = 'not_initialized'
        except Exception as e:
            status['components']['database'] = f'error: {str(e)}'

        # Check authentication manager
        try:
            if self.auth_manager:
                # Check if auth database is accessible
                status['components']['authentication'] = 'healthy'
            else:
                status['components']['authentication'] = 'not_initialized'
        except Exception as e:
            status['components']['authentication'] = f'error: {str(e)}'

        # Check other components
        status['components']['stats_calculator'] = 'healthy' if self.stats_calculator else 'not_initialized'
        status['components']['ui_manager'] = 'healthy' if self.ui_manager else 'not_initialized'
        status['components']['offline_manager'] = 'healthy' if self.offline_manager else 'disabled'
        status['components']['export_manager'] = 'healthy' if self.export_manager else 'disabled'

        # Include deployment health check
        try:
            deployment_health = self.deployment_manager.check_deployment_health()
            status['deployment'] = deployment_health
        except Exception as e:
            status['deployment'] = {'status': 'error', 'error': str(e)}

        return status

    def shutdown(self) -> None:
        """
        Gracefully shutdown the application and cleanup resources.
        """
        try:
            self.logger.info("Shutting down Pachinko Revenue Calculator...")

            # Cleanup components in reverse order
            if self.ui_manager:
                # UI manager doesn't need explicit cleanup
                pass

            if self.offline_manager:
                # Sync any pending offline data
                try:
                    self.offline_manager.sync_with_server()
                except Exception as e:
                    self.logger.warning(
                        f"Failed to sync offline data during shutdown: {e}")

            if self.db_manager:
                # Database manager handles its own cleanup
                pass

            if self.auth_manager:
                # Authentication manager handles its own cleanup
                pass

            self.is_initialized = False
            self.logger.info("Application shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
