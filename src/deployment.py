"""
Deployment configuration and free tier limit management.

Handles Streamlit Cloud deployment settings, monitors resource usage,
and implements free tier compliance checks.
"""

import os
import time
import logging
import streamlit as st
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import psutil
import sys

from .config import get_config


class DeploymentManager:
    """
    Manages deployment-specific functionality and free tier compliance.

    Monitors resource usage, enforces limits, and provides deployment
    health checks for Streamlit Cloud deployment.
    """

    def __init__(self):
        """Initialize deployment manager."""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self._usage_cache = {}
        self._cache_timeout = 60  # Cache usage data for 1 minute

    def check_deployment_health(self) -> Dict[str, Any]:
        """
        Check deployment health status.

        Returns:
            Dictionary with health check results
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        try:
            # Database connectivity check
            health_status['checks']['database'] = self._check_database_health()

            # Memory usage check
            health_status['checks']['memory'] = self._check_memory_usage()

            # Free tier compliance check
            health_status['checks']['free_tier'] = self._check_free_tier_compliance()

            # Configuration validation
            health_status['checks']['configuration'] = self._check_configuration()

            # Determine overall status
            failed_checks = [k for k, v in health_status['checks'].items()
                             if not v.get('status', True)]

            if failed_checks:
                health_status['status'] = 'degraded' if len(
                    failed_checks) == 1 else 'unhealthy'
                health_status['failed_checks'] = failed_checks

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)

        return health_status

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from .database import DatabaseManager

            db_manager = DatabaseManager()
            start_time = time.time()

            # Simple connectivity test
            db_manager._get_connection()

            response_time = time.time() - start_time

            return {
                'status': True,
                'response_time_ms': round(response_time * 1000, 2),
                'message': 'Database connection successful'
            }

        except Exception as e:
            return {
                'status': False,
                'error': str(e),
                'message': 'Database connection failed'
            }

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage and limits."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # Streamlit Cloud typically has ~1GB memory limit
            memory_limit_mb = 1024
            memory_usage_percent = (memory_mb / memory_limit_mb) * 100

            status = memory_usage_percent < 80  # Warning at 80%

            return {
                'status': status,
                'memory_mb': round(memory_mb, 2),
                'memory_limit_mb': memory_limit_mb,
                'usage_percent': round(memory_usage_percent, 2),
                'message': f'Memory usage: {memory_usage_percent:.1f}%'
            }

        except Exception as e:
            return {
                'status': False,
                'error': str(e),
                'message': 'Memory check failed'
            }

    def _check_free_tier_compliance(self) -> Dict[str, Any]:
        """Check compliance with free tier limits."""
        try:
            current_usage = self.get_current_usage()
            compliance = self.config.check_free_tier_compliance(current_usage)

            all_compliant = all(compliance.values())
            violations = [k for k, v in compliance.items() if not v]

            return {
                'status': all_compliant,
                'compliance': compliance,
                'violations': violations,
                'current_usage': current_usage,
                'message': 'All limits compliant' if all_compliant else f'Violations: {violations}'
            }

        except Exception as e:
            return {
                'status': False,
                'error': str(e),
                'message': 'Free tier compliance check failed'
            }

    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            # Check required environment variables for production
            if self.config.is_production():
                required_vars = [
                    'DATABASE_URL',
                    'SECRET_KEY',
                    'ENCRYPTION_KEY'
                ]

                missing_vars = []
                for var in required_vars:
                    if not os.getenv(var):
                        missing_vars.append(var)

                if missing_vars:
                    return {
                        'status': False,
                        'missing_variables': missing_vars,
                        'message': f'Missing required environment variables: {missing_vars}'
                    }

            return {
                'status': True,
                'message': 'Configuration valid'
            }

        except Exception as e:
            return {
                'status': False,
                'error': str(e),
                'message': 'Configuration check failed'
            }

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage statistics.

        Returns:
            Dictionary with current usage metrics
        """
        cache_key = 'usage_stats'
        current_time = time.time()

        # Check cache
        if (cache_key in self._usage_cache and
                current_time - self._usage_cache[cache_key]['timestamp'] < self._cache_timeout):
            return self._usage_cache[cache_key]['data']

        try:
            from .database import DatabaseManager

            db_manager = DatabaseManager()

            # Get database usage statistics
            usage_stats = {
                'users': self._get_user_count(db_manager),
                'max_sessions_per_user': self._get_max_sessions_per_user(db_manager),
                'db_size_mb': self._get_database_size_mb(db_manager),
                'bandwidth_mb': self._estimate_bandwidth_usage(),
                'timestamp': current_time
            }

            # Cache the results
            self._usage_cache[cache_key] = {
                'data': usage_stats,
                'timestamp': current_time
            }

            return usage_stats

        except Exception as e:
            self.logger.error(f"Failed to get usage statistics: {e}")
            return {
                'users': 0,
                'max_sessions_per_user': 0,
                'db_size_mb': 0,
                'bandwidth_mb': 0,
                'error': str(e)
            }

    def _get_user_count(self, db_manager) -> int:
        """Get total number of users."""
        try:
            query = "SELECT COUNT(DISTINCT user_id) FROM game_sessions"
            result = db_manager.execute_query(query)
            return result[0][0] if result else 0
        except:
            return 0

    def _get_max_sessions_per_user(self, db_manager) -> int:
        """Get maximum number of sessions per user."""
        try:
            query = """
            SELECT MAX(session_count) FROM (
                SELECT user_id, COUNT(*) as session_count 
                FROM game_sessions 
                GROUP BY user_id
            ) user_sessions
            """
            result = db_manager.execute_query(query)
            return result[0][0] if result and result[0][0] else 0
        except:
            return 0

    def _get_database_size_mb(self, db_manager) -> float:
        """Estimate database size in MB."""
        try:
            if self.config.get('database.type') == 'postgresql':
                # For PostgreSQL, get table sizes
                query = """
                SELECT pg_size_pretty(pg_total_relation_size('game_sessions'))
                """
                result = db_manager.execute_query(query)
                # This is a rough estimate - in production you'd parse the result
                return 1.0  # Placeholder
            else:
                # For SQLite, get file size
                db_path = self.config.get('database.path')
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    return size_bytes / 1024 / 1024
                return 0.0
        except:
            return 0.0

    def _estimate_bandwidth_usage(self) -> float:
        """Estimate bandwidth usage (rough calculation)."""
        # This is a simplified estimation
        # In production, you'd track actual bandwidth usage
        try:
            # Estimate based on session state and typical request sizes
            if hasattr(st.session_state, 'page_views'):
                page_views = st.session_state.page_views
                # Rough estimate: 100KB per page view
                return (page_views * 0.1)  # MB
            return 0.0
        except:
            return 0.0

    def enforce_free_tier_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Enforce free tier limits and return status.

        Returns:
            Tuple of (allowed, error_message)
        """
        try:
            current_usage = self.get_current_usage()
            compliance = self.config.check_free_tier_compliance(current_usage)
            limits = self.config.get_free_tier_limits()

            # Check each limit
            if not compliance['users']:
                return False, f"ユーザー数制限に達しました (最大: {limits['max_users']}人)"

            if not compliance['sessions_per_user']:
                return False, f"1ユーザーあたりのセッション数制限に達しました (最大: {limits['max_sessions_per_user']}セッション)"

            if not compliance['db_size']:
                return False, f"データベースサイズ制限に達しました (最大: {limits['max_db_size_mb']}MB)"

            if not compliance['bandwidth']:
                return False, f"帯域幅制限に達しました (最大: {limits['max_bandwidth_mb']}MB/月)"

            return True, None

        except Exception as e:
            self.logger.error(f"Failed to enforce limits: {e}")
            return True, None  # Allow operation if check fails

    def display_usage_dashboard(self):
        """Display usage dashboard in Streamlit."""
        st.subheader("📊 リソース使用状況")

        try:
            current_usage = self.get_current_usage()
            limits = self.config.get_free_tier_limits()
            compliance = self.config.check_free_tier_compliance(current_usage)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                users_percent = (
                    current_usage['users'] / limits['max_users']) * 100
                st.metric(
                    "ユーザー数",
                    f"{current_usage['users']}/{limits['max_users']}",
                    f"{users_percent:.1f}%"
                )
                if not compliance['users']:
                    st.error("制限に達しています")

            with col2:
                sessions_percent = (
                    current_usage['max_sessions_per_user'] / limits['max_sessions_per_user']) * 100
                st.metric(
                    "最大セッション数",
                    f"{current_usage['max_sessions_per_user']}/{limits['max_sessions_per_user']}",
                    f"{sessions_percent:.1f}%"
                )
                if not compliance['sessions_per_user']:
                    st.error("制限に達しています")

            with col3:
                db_percent = (
                    current_usage['db_size_mb'] / limits['max_db_size_mb']) * 100
                st.metric(
                    "DB使用量 (MB)",
                    f"{current_usage['db_size_mb']:.1f}/{limits['max_db_size_mb']}",
                    f"{db_percent:.1f}%"
                )
                if not compliance['db_size']:
                    st.error("制限に達しています")

            with col4:
                bandwidth_percent = (
                    current_usage['bandwidth_mb'] / limits['max_bandwidth_mb']) * 100
                st.metric(
                    "帯域幅 (MB)",
                    f"{current_usage['bandwidth_mb']:.1f}/{limits['max_bandwidth_mb']}",
                    f"{bandwidth_percent:.1f}%"
                )
                if not compliance['bandwidth']:
                    st.error("制限に達しています")

            # Health status
            health = self.check_deployment_health()

            if health['status'] == 'healthy':
                st.success("✅ システム正常")
            elif health['status'] == 'degraded':
                st.warning("⚠️ システム軽微な問題")
            else:
                st.error("❌ システム問題あり")

        except Exception as e:
            st.error(f"使用状況の取得に失敗しました: {e}")

    def get_deployment_info(self) -> Dict[str, Any]:
        """
        Get deployment information.

        Returns:
            Dictionary with deployment details
        """
        return {
            'platform': self.config.get('deployment.platform'),
            'environment': self.config.get('environment'),
            'python_version': sys.version,
            'streamlit_version': st.__version__,
            'database_type': self.config.get('database.type'),
            'features_enabled': {
                'offline_mode': self.config.get('features.offline_mode'),
                'export_enabled': self.config.get('features.export_enabled'),
                'advanced_stats': self.config.get('features.advanced_stats'),
                'animations': self.config.get('ui.enable_animations')
            },
            'free_tier_limits': self.config.get_free_tier_limits(),
            'deployment_time': datetime.now().isoformat()
        }


# Global deployment manager instance
_deployment_manager: Optional[DeploymentManager] = None


def get_deployment_manager() -> DeploymentManager:
    """
    Get the global deployment manager instance.

    Returns:
        DeploymentManager instance
    """
    global _deployment_manager

    if _deployment_manager is None:
        _deployment_manager = DeploymentManager()

    return _deployment_manager
