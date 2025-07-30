"""
Comprehensive error handling system for the Pachinko Revenue Calculator application.

Provides centralized error handling, user-friendly error messages, and logging functionality.
"""

import logging
import streamlit as st
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import os
import sys

from .exceptions import ErrorSeverity, ErrorCategory, DatabaseError, ValidationError, AuthenticationError


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification."""
    VALIDATION = "validation"
    DATABASE = "database"
    UI = "ui"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    EXPORT = "export"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class PachinkoError(Exception):
    """Base exception class for Pachinko application errors."""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[Dict] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(message)


class UIError(PachinkoError):
    """Exception for UI-related errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.UI, severity, details)


class NetworkError(PachinkoError):
    """Exception for network-related errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.NETWORK, severity, details)


class ExportError(PachinkoError):
    """Exception for export-related errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.EXPORT, severity, details)


class AuthenticationError(PachinkoError):
    """Exception for authentication-related errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.AUTHENTICATION, severity, details)


class SystemError(PachinkoError):
    """Exception for system-level errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.CRITICAL, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.SYSTEM, severity, details)


class ErrorHandler:
    """
    Centralized error handling system for the Pachinko Revenue Calculator.

    Provides comprehensive error handling with user-friendly messages, logging,
    and recovery suggestions based on error types and severity levels.
    """

    def __init__(self, log_file: str = "pachinko_app.log", log_level: int = logging.INFO):
        """
        Initialize the error handler.

        Args:
            log_file: Path to the log file
            log_level: Logging level (default: INFO)
        """
        self.log_file = log_file
        self.log_level = log_level
        self.logger = self._setup_logger()

        # Error message templates for user-friendly display
        self.error_messages = self._initialize_error_messages()

        # Recovery suggestions for different error types
        self.recovery_suggestions = self._initialize_recovery_suggestions()

        # Error statistics for monitoring
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'last_error_time': None
        }

    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logging system with proper formatting and handlers.

        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger('pachinko_app')
        logger.setLevel(self.log_level)

        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler for persistent logging
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.log_file) if os.path.dirname(
                self.log_file) else '.'
            os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, continue with console logging only
            logger.warning(f"Failed to set up file logging: {e}")

        return logger

    def _initialize_error_messages(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize user-friendly error messages for different error types.

        Returns:
            Dict: Error message templates organized by category and type
        """
        return {
            'validation': {
                'required_field': '必須項目が入力されていません: {field}',
                'invalid_format': '入力形式が正しくありません: {field}',
                'invalid_range': '入力値が範囲外です: {field}',
                'invalid_date': '日付の入力が正しくありません',
                'invalid_time': '時間の入力が正しくありません',
                'invalid_amount': '金額の入力が正しくありません',
                'future_date': '未来の日付は入力できません',
                'invalid_session': 'セッションデータが不正です'
            },
            'database': {
                'connection_failed': 'データベースに接続できませんでした',
                'save_failed': 'データの保存に失敗しました',
                'load_failed': 'データの読み込みに失敗しました',
                'delete_failed': 'データの削除に失敗しました',
                'integrity_error': 'データの整合性エラーが発生しました',
                'not_found': '指定されたデータが見つかりません',
                'duplicate_entry': '重複するデータが存在します'
            },
            'ui': {
                'page_load_failed': 'ページの読み込みに失敗しました',
                'form_submission_failed': 'フォームの送信に失敗しました',
                'navigation_failed': 'ページ遷移に失敗しました',
                'component_error': 'UI コンポーネントでエラーが発生しました',
                'session_state_error': 'セッション状態の管理でエラーが発生しました',
                'browser_compatibility': 'お使いのブラウザはサポートされていません'
            },
            'authentication': {
                'login_failed': 'ログインに失敗しました',
                'invalid_credentials': 'ユーザー名またはパスワードが正しくありません',
                'session_expired': 'セッションの有効期限が切れました',
                'access_denied': 'アクセスが拒否されました',
                'account_locked': 'アカウントがロックされています',
                'password_weak': 'パスワードが安全性の要件を満たしていません'
            },
            'network': {
                'connection_lost': 'ネットワーク接続が失われました',
                'sync_failed': 'データの同期に失敗しました',
                'offline_mode': 'オフラインモードで動作しています',
                'server_error': 'サーバーエラーが発生しました',
                'timeout': '通信がタイムアウトしました'
            },
            'export': {
                'export_failed': 'データのエクスポートに失敗しました',
                'file_creation_failed': 'ファイルの作成に失敗しました',
                'invalid_format': 'エクスポート形式が正しくありません',
                'no_data': 'エクスポートするデータがありません',
                'permission_denied': 'ファイルの書き込み権限がありません'
            },
            'system': {
                'memory_error': 'メモリ不足が発生しました',
                'disk_space_error': 'ディスク容量が不足しています',
                'permission_error': 'システム権限が不足しています',
                'configuration_error': '設定エラーが発生しました',
                'dependency_error': '依存関係のエラーが発生しました'
            }
        }

    def _initialize_recovery_suggestions(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize recovery suggestions for different error types.

        Returns:
            Dict: Recovery suggestions organized by category and type
        """
        return {
            'validation': {
                'required_field': '必須項目をすべて入力してください',
                'invalid_format': '正しい形式で入力し直してください',
                'invalid_range': '有効な範囲内の値を入力してください',
                'invalid_date': '正しい日付形式（YYYY/MM/DD）で入力してください',
                'invalid_time': '正しい時間形式（HH:MM）で入力してください',
                'invalid_amount': '正の整数で金額を入力してください',
                'future_date': '今日以前の日付を選択してください',
                'invalid_session': 'セッションデータを確認し、正しい値を入力してください'
            },
            'database': {
                'connection_failed': 'しばらく待ってから再試行してください。問題が続く場合は管理者にお問い合わせください',
                'save_failed': 'データを確認して再度保存してください',
                'load_failed': 'ページを再読み込みしてください',
                'delete_failed': '削除対象のデータが存在するか確認してください',
                'integrity_error': 'データの整合性を確認し、正しい値を入力してください',
                'not_found': '存在するデータを選択してください',
                'duplicate_entry': '重複しない値を入力してください'
            },
            'ui': {
                'page_load_failed': 'ページを再読み込みしてください',
                'form_submission_failed': 'フォームの内容を確認して再送信してください',
                'navigation_failed': 'ブラウザを再読み込みしてください',
                'component_error': 'ページを再読み込みしてください',
                'session_state_error': 'ブラウザを再読み込みしてください',
                'browser_compatibility': 'Chrome、Firefox、Safari の最新版をご利用ください'
            },
            'authentication': {
                'login_failed': 'ユーザー名とパスワードを確認して再度ログインしてください',
                'invalid_credentials': '正しいユーザー名とパスワードを入力してください',
                'session_expired': '再度ログインしてください',
                'access_denied': '管理者にアクセス権限をお問い合わせください',
                'account_locked': 'しばらく待ってから再度ログインしてください',
                'password_weak': '8文字以上で英数字を含むパスワードを設定してください'
            },
            'network': {
                'connection_lost': 'ネットワーク接続を確認してください',
                'sync_failed': 'ネットワーク接続を確認して再度同期してください',
                'offline_mode': 'ネットワーク接続が復旧すると自動的に同期されます',
                'server_error': 'しばらく待ってから再試行してください',
                'timeout': 'ネットワーク接続を確認して再試行してください'
            },
            'export': {
                'export_failed': 'データを確認して再度エクスポートしてください',
                'file_creation_failed': 'ディスク容量と権限を確認してください',
                'invalid_format': 'サポートされている形式（CSV、PDF）を選択してください',
                'no_data': 'エクスポートするデータを作成してください',
                'permission_denied': 'ファイルの書き込み権限を確認してください'
            },
            'system': {
                'memory_error': 'アプリケーションを再起動してください',
                'disk_space_error': 'ディスク容量を確保してください',
                'permission_error': '管理者権限で実行してください',
                'configuration_error': '設定ファイルを確認してください',
                'dependency_error': '必要なライブラリがインストールされているか確認してください'
            }
        }

    def handle_error(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity,
                     context: Optional[Dict[str, Any]] = None, show_user_message: bool = True) -> None:
        """
        Handle an error with comprehensive logging and user notification.

        Args:
            error: The exception that occurred
            category: Error category
            severity: Error severity
            context: Additional context information
            show_user_message: Whether to show user-friendly message in Streamlit
        """
        # Update error statistics
        self._update_error_stats(error)

        # Create error details
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': category.value,
            'severity': severity.value,
            'timestamp': datetime.now().isoformat(),
            'context': context if isinstance(context, dict) else {} if context is None else {'info': str(context)},
            'traceback': traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }

        # Log the error
        self._log_error(error, error_details)

        # Show user-friendly message if requested
        if show_user_message:
            self._show_user_error_message(error, category, severity)

    def _categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """
        Categorize an error and determine its severity.

        Args:
            error: The exception to categorize

        Returns:
            tuple: (ErrorCategory, ErrorSeverity)
        """
        if isinstance(error, ValidationError):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        elif isinstance(error, DatabaseError):
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH
        elif isinstance(error, UIError):
            return ErrorCategory.UI, error.severity
        elif isinstance(error, NetworkError):
            return ErrorCategory.NETWORK, error.severity
        elif isinstance(error, ExportError):
            return ErrorCategory.EXPORT, error.severity
        elif isinstance(error, AuthenticationError):
            return ErrorCategory.AUTHENTICATION, error.severity
        elif isinstance(error, SystemError):
            return ErrorCategory.SYSTEM, error.severity
        elif isinstance(error, PachinkoError):
            return error.category, error.severity
        elif isinstance(error, (MemoryError, OSError)):
            return ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH
        elif isinstance(error, PermissionError):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        else:
            return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    def _log_error(self, error: Exception, error_details: Dict[str, Any]) -> None:
        """
        Log an error with appropriate level based on severity.

        Args:
            error: The exception that occurred
            error_details: Detailed error information
        """
        severity = ErrorSeverity(error_details['severity'])
        category = error_details['category']
        message = f"[{category.upper()}] {error_details['error_message']}"

        # Add context if available
        if error_details['context']:
            try:
                if isinstance(error_details['context'], dict):
                    context_str = ', '.join(
                        [f"{k}={v}" for k, v in error_details['context'].items()])
                else:
                    context_str = str(error_details['context'])
                message += f" | Context: {context_str}"
            except Exception as ctx_error:
                message += f" | Context: {str(error_details['context'])}"

        # Log with appropriate level
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(message)
        else:  # LOW
            self.logger.info(message)

    def _show_user_error_message(self, error: Exception, category: ErrorCategory,
                                 severity: ErrorSeverity) -> None:
        """
        Show a user-friendly error message in Streamlit.

        Args:
            error: The exception that occurred
            category: Error category
            severity: Error severity
        """
        # Get user-friendly message
        user_message = self._get_user_friendly_message(error, category)

        # Get recovery suggestion
        recovery_suggestion = self._get_recovery_suggestion(error, category)

        # Choose Streamlit display method based on severity
        if severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 **重大なエラー**: {user_message}")
            if recovery_suggestion:
                st.error(f"**対処方法**: {recovery_suggestion}")
            st.error("**このエラーが続く場合は、アプリケーションを再起動してください。**")
        elif severity == ErrorSeverity.HIGH:
            st.error(f"❌ **エラー**: {user_message}")
            if recovery_suggestion:
                st.info(f"💡 **対処方法**: {recovery_suggestion}")
        elif severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ **警告**: {user_message}")
            if recovery_suggestion:
                st.info(f"💡 **対処方法**: {recovery_suggestion}")
        else:  # LOW
            st.info(f"ℹ️ **情報**: {user_message}")
            if recovery_suggestion:
                st.info(f"💡 **対処方法**: {recovery_suggestion}")

    def _get_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """
        Get a user-friendly error message.

        Args:
            error: The exception that occurred
            category: Error category

        Returns:
            str: User-friendly error message
        """
        category_messages = self.error_messages.get(category.value, {})

        # Try to match specific error types
        if isinstance(error, ValidationError):
            if 'required' in str(error).lower():
                return category_messages.get('required_field', str(error)).format(field=error.field_name)
            elif 'format' in str(error).lower() or 'invalid' in str(error).lower():
                return category_messages.get('invalid_format', str(error)).format(field=error.field_name)
            else:
                return str(error)
        elif isinstance(error, DatabaseError):
            error_str = str(error).lower()
            if 'connection' in error_str:
                return category_messages.get('connection_failed', str(error))
            elif 'save' in error_str or 'insert' in error_str or 'create' in error_str:
                return category_messages.get('save_failed', str(error))
            elif 'load' in error_str or 'select' in error_str or 'get' in error_str:
                return category_messages.get('load_failed', str(error))
            elif 'delete' in error_str:
                return category_messages.get('delete_failed', str(error))
            elif 'not found' in error_str:
                return category_messages.get('not_found', str(error))
            else:
                return category_messages.get('integrity_error', str(error))
        elif isinstance(error, PachinkoError):
            return error.message
        else:
            # Generic message based on category
            return category_messages.get('generic', str(error))

    def _get_recovery_suggestion(self, error: Exception, category: ErrorCategory) -> Optional[str]:
        """
        Get a recovery suggestion for the error.

        Args:
            error: The exception that occurred
            category: Error category

        Returns:
            str: Recovery suggestion or None
        """
        category_suggestions = self.recovery_suggestions.get(
            category.value, {})

        # Try to match specific error types
        if isinstance(error, ValidationError):
            if 'required' in str(error).lower():
                return category_suggestions.get('required_field')
            elif 'format' in str(error).lower() or 'invalid' in str(error).lower():
                return category_suggestions.get('invalid_format')
            elif 'date' in str(error).lower():
                return category_suggestions.get('invalid_date')
            elif 'time' in str(error).lower():
                return category_suggestions.get('invalid_time')
            elif 'amount' in str(error).lower() or '金額' in str(error):
                return category_suggestions.get('invalid_amount')
            else:
                return category_suggestions.get('invalid_format')
        elif isinstance(error, DatabaseError):
            error_str = str(error).lower()
            if 'connection' in error_str:
                return category_suggestions.get('connection_failed')
            elif 'save' in error_str or 'insert' in error_str:
                return category_suggestions.get('save_failed')
            elif 'load' in error_str or 'select' in error_str:
                return category_suggestions.get('load_failed')
            elif 'delete' in error_str:
                return category_suggestions.get('delete_failed')
            elif 'not found' in error_str:
                return category_suggestions.get('not_found')
            else:
                return category_suggestions.get('integrity_error')
        else:
            # Generic suggestion based on category
            return category_suggestions.get('generic')

    def _update_error_stats(self, error: Exception) -> None:
        """
        Update error statistics for monitoring.

        Args:
            error: The exception that occurred
        """
        self.error_stats['total_errors'] += 1
        self.error_stats['last_error_time'] = datetime.now()

        # Update category stats
        category, severity = self._categorize_error(error)
        category_key = category.value
        severity_key = severity.value

        if category_key not in self.error_stats['errors_by_category']:
            self.error_stats['errors_by_category'][category_key] = 0
        self.error_stats['errors_by_category'][category_key] += 1

        if severity_key not in self.error_stats['errors_by_severity']:
            self.error_stats['errors_by_severity'][severity_key] = 0
        self.error_stats['errors_by_severity'][severity_key] += 1

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get current error statistics.

        Returns:
            Dict: Error statistics
        """
        return self.error_stats.copy()

    def clear_error_stats(self) -> None:
        """Clear error statistics."""
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'last_error_time': None
        }

    @staticmethod
    def safe_execute(func: Callable, *args, error_handler: Optional['ErrorHandler'] = None,
                     context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        Safely execute a function with error handling.

        Args:
            func: Function to execute
            *args: Function arguments
            error_handler: Error handler instance (optional)
            context: Additional context for error handling
            **kwargs: Function keyword arguments

        Returns:
            Function result or None if error occurred
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if error_handler:
                error_handler.handle_error(e, context)
            else:
                # Fallback error handling
                st.error(f"エラーが発生しました: {str(e)}")
            return None

    def create_error_boundary(self, component_name: str) -> Callable:
        """
        Create an error boundary decorator for UI components.

        Args:
            component_name: Name of the component for context

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    context = {
                        'component': component_name,
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                    self.handle_error(e, context)
                    return None
            return wrapper
        return decorator


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        ErrorHandler: Global error handler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(error: Exception, category: ErrorCategory, severity: ErrorSeverity,
                 context: Optional[Dict[str, Any]] = None, show_user_message: bool = True) -> None:
    """
    Convenience function to handle errors using the global error handler.

    Args:
        error: The exception that occurred
        category: Error category
        severity: Error severity
        context: Additional context information
        show_user_message: Whether to show user-friendly message in Streamlit
    """
    try:
        error_handler = get_error_handler()
        error_handler.handle_error(
            error, category, severity, context, show_user_message)
    except Exception as handler_error:
        # Fallback error handling
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handler failed: {handler_error}")
        logger.error(f"Original error: {error}")


def safe_execute(func: Callable, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    """
    Convenience function to safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        context: Additional context for error handling
        **kwargs: Function keyword arguments

    Returns:
        Function result or None if error occurred
    """
    error_handler = get_error_handler()
    return ErrorHandler.safe_execute(func, *args, error_handler=error_handler, context=context, **kwargs)
