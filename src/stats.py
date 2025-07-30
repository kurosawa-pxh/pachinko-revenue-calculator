"""
Statistics calculation engine for the Pachinko Revenue Calculator application.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .models import GameSession
from .database import DatabaseManager
from .exceptions import DatabaseError


@dataclass
class BasicStats:
    """Basic statistics data structure."""
    total_sessions: int
    completed_sessions: int
    total_investment: int
    total_return: int
    total_profit: int
    winning_sessions: int
    losing_sessions: int
    win_rate: float
    avg_investment: float
    avg_profit: float
    avg_return: float
    max_profit: int
    min_profit: int
    profit_variance: float


@dataclass
class MonthlyStats:
    """Monthly statistics data structure."""
    year: int
    month: int
    basic_stats: BasicStats
    daily_profits: Dict[int, int]  # day -> profit
    sessions_by_day: Dict[int, int]  # day -> session count


@dataclass
class MachineStats:
    """Machine-specific statistics data structure."""
    machine_name: str
    basic_stats: BasicStats
    store_distribution: Dict[str, int]  # store_name -> session count
    avg_session_duration: Optional[float]  # in minutes
    performance_score: float = 0.0  # Composite performance score


class StatsCalculator:
    """
    Statistics calculation engine for pachinko game sessions.

    Provides comprehensive statistical analysis including basic stats,
    monthly breakdowns, and machine-specific performance metrics.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the statistics calculator.

        Args:
            db_manager: Database manager instance for data access
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    def calculate_session_profit(self, investment: int, return_amount: int) -> int:
        """
        Calculate profit/loss for a single session.

        Args:
            investment: Total amount invested
            return_amount: Total amount returned

        Returns:
            int: Profit (positive) or loss (negative)
        """
        return return_amount - investment

    def calculate_basic_stats(self, sessions: List[GameSession]) -> BasicStats:
        """
        Calculate basic statistics from a list of game sessions.

        Args:
            sessions: List of GameSession objects

        Returns:
            BasicStats: Comprehensive basic statistics

        Raises:
            ValueError: If sessions list is empty or contains invalid data
        """
        if not sessions:
            return self._empty_basic_stats()

        try:
            # Filter only completed sessions for calculations
            completed_sessions = [
                s for s in sessions if s.is_completed and s.profit is not None]

            if not completed_sessions:
                return self._empty_basic_stats()

            total_sessions = len(sessions)
            completed_count = len(completed_sessions)

            # Calculate totals
            total_investment = sum(
                s.final_investment for s in completed_sessions)
            total_return = sum(s.return_amount for s in completed_sessions)
            total_profit = sum(s.profit for s in completed_sessions)

            # Calculate win/loss counts
            winning_sessions = len(
                [s for s in completed_sessions if s.profit > 0])
            losing_sessions = len(
                [s for s in completed_sessions if s.profit < 0])

            # Calculate rates and averages
            win_rate = (winning_sessions / completed_count *
                        100) if completed_count > 0 else 0
            avg_investment = total_investment / completed_count if completed_count > 0 else 0
            avg_profit = total_profit / completed_count if completed_count > 0 else 0
            avg_return = total_return / completed_count if completed_count > 0 else 0

            # Calculate min/max profits
            profits = [s.profit for s in completed_sessions]
            max_profit = max(profits) if profits else 0
            min_profit = min(profits) if profits else 0

            # Calculate profit variance
            if completed_count > 1:
                mean_profit = avg_profit
                profit_variance = sum(
                    (p - mean_profit) ** 2 for p in profits) / (completed_count - 1)
            else:
                profit_variance = 0

            self.logger.info(
                f"Calculated basic stats for {total_sessions} sessions ({completed_count} completed)")

            return BasicStats(
                total_sessions=total_sessions,
                completed_sessions=completed_count,
                total_investment=total_investment,
                total_return=total_return,
                total_profit=total_profit,
                winning_sessions=winning_sessions,
                losing_sessions=losing_sessions,
                win_rate=win_rate,
                avg_investment=avg_investment,
                avg_profit=avg_profit,
                avg_return=avg_return,
                max_profit=max_profit,
                min_profit=min_profit,
                profit_variance=profit_variance
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate basic stats: {e}")
            raise ValueError(f"Statistics calculation failed: {e}")

    def get_user_basic_stats(self, user_id: str, date_range: Optional[Tuple[datetime, datetime]] = None) -> BasicStats:
        """
        Get basic statistics for a user with optional date filtering.

        Args:
            user_id: User ID to calculate stats for
            date_range: Optional tuple of (start_date, end_date) for filtering

        Returns:
            BasicStats: User's basic statistics

        Raises:
            DatabaseError: If database query fails
        """
        try:
            sessions = self.db_manager.get_sessions(user_id, date_range)
            return self.calculate_basic_stats(sessions)

        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get user basic stats: {e}")
            raise ValueError(f"User statistics calculation failed: {e}")

    def _empty_basic_stats(self) -> BasicStats:
        """
        Return empty basic statistics structure.

        Returns:
            BasicStats: Empty statistics with all values set to 0
        """
        return BasicStats(
            total_sessions=0,
            completed_sessions=0,
            total_investment=0,
            total_return=0,
            total_profit=0,
            winning_sessions=0,
            losing_sessions=0,
            win_rate=0.0,
            avg_investment=0.0,
            avg_profit=0.0,
            avg_return=0.0,
            max_profit=0,
            min_profit=0,
            profit_variance=0.0
        )

    def _calculate_session_duration(self, session: GameSession) -> Optional[float]:
        """
        Calculate session duration in minutes.

        Args:
            session: GameSession object

        Returns:
            float: Duration in minutes, or None if not calculable
        """
        if not session.is_completed or not session.end_time or not session.start_time:
            return None

        duration = session.end_time - session.start_time
        return duration.total_seconds() / 60  # Convert to minutes

    def calculate_monthly_stats(self, user_id: str, year: int, month: int) -> MonthlyStats:
        """
        Calculate monthly statistics for a specific user, year, and month.

        Args:
            user_id: User ID to calculate stats for
            year: Year to calculate stats for
            month: Month to calculate stats for (1-12)

        Returns:
            MonthlyStats: Monthly statistics data

        Raises:
            DatabaseError: If database query fails
            ValueError: If invalid year/month provided
        """
        if not (1 <= month <= 12):
            raise ValueError(
                f"Invalid month: {month}. Must be between 1 and 12")

        if year < 2000 or year > datetime.now().year + 1:
            raise ValueError(f"Invalid year: {year}")

        try:
            # Create date range for the specific month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            # Get sessions for the month
            sessions = self.db_manager.get_sessions(
                user_id, (start_date, end_date))

            # Calculate basic stats for the month
            basic_stats = self.calculate_basic_stats(sessions)

            # Calculate daily breakdown
            daily_profits = {}
            sessions_by_day = {}

            completed_sessions = [
                s for s in sessions if s.is_completed and s.profit is not None]

            for session in completed_sessions:
                day = session.date.day

                # Accumulate daily profits
                if day not in daily_profits:
                    daily_profits[day] = 0
                daily_profits[day] += session.profit

                # Count sessions by day
                if day not in sessions_by_day:
                    sessions_by_day[day] = 0
                sessions_by_day[day] += 1

            self.logger.info(
                f"Calculated monthly stats for {user_id}: {year}/{month:02d} - {len(sessions)} sessions")

            return MonthlyStats(
                year=year,
                month=month,
                basic_stats=basic_stats,
                daily_profits=daily_profits,
                sessions_by_day=sessions_by_day
            )

        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate monthly stats: {e}")
            raise ValueError(f"Monthly statistics calculation failed: {e}")

    def get_monthly_stats_range(self, user_id: str, start_year: int, start_month: int,
                                end_year: int, end_month: int) -> List[MonthlyStats]:
        """
        Get monthly statistics for a range of months.

        Args:
            user_id: User ID to calculate stats for
            start_year: Starting year
            start_month: Starting month (1-12)
            end_year: Ending year
            end_month: Ending month (1-12)

        Returns:
            List[MonthlyStats]: List of monthly statistics in chronological order

        Raises:
            ValueError: If invalid date range provided
        """
        if start_year > end_year or (start_year == end_year and start_month > end_month):
            raise ValueError("Start date must be before or equal to end date")

        monthly_stats = []
        current_year = start_year
        current_month = start_month

        try:
            while current_year < end_year or (current_year == end_year and current_month <= end_month):
                stats = self.calculate_monthly_stats(
                    user_id, current_year, current_month)
                monthly_stats.append(stats)

                # Move to next month
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1

            self.logger.info(
                f"Calculated stats for {len(monthly_stats)} months")
            return monthly_stats

        except Exception as e:
            self.logger.error(f"Failed to calculate monthly stats range: {e}")
            raise ValueError(f"Monthly stats range calculation failed: {e}")

    def get_monthly_comparison(self, user_id: str, months: List[Tuple[int, int]]) -> Dict[str, Any]:
        """
        Compare statistics across multiple months.

        Args:
            user_id: User ID to calculate stats for
            months: List of (year, month) tuples to compare

        Returns:
            Dict containing comparison data and trends
        """
        if not months:
            raise ValueError(
                "At least one month must be provided for comparison")

        try:
            monthly_data = []
            for year, month in months:
                stats = self.calculate_monthly_stats(user_id, year, month)
                monthly_data.append({
                    'year': year,
                    'month': month,
                    'stats': stats
                })

            # Calculate trends and comparisons
            profits = [
                data['stats'].basic_stats.total_profit for data in monthly_data]
            win_rates = [
                data['stats'].basic_stats.win_rate for data in monthly_data]
            investments = [
                data['stats'].basic_stats.total_investment for data in monthly_data]

            comparison = {
                'months_data': monthly_data,
                'best_month': None,
                'worst_month': None,
                'profit_trend': self._calculate_trend(profits),
                'win_rate_trend': self._calculate_trend(win_rates),
                'investment_trend': self._calculate_trend(investments),
                'total_profit': sum(profits),
                'avg_monthly_profit': sum(profits) / len(profits) if profits else 0,
                'profit_volatility': self._calculate_volatility(profits)
            }

            # Find best and worst months
            if monthly_data:
                best_idx = profits.index(max(profits))
                worst_idx = profits.index(min(profits))
                comparison['best_month'] = monthly_data[best_idx]
                comparison['worst_month'] = monthly_data[worst_idx]

            return comparison

        except Exception as e:
            self.logger.error(f"Failed to calculate monthly comparison: {e}")
            raise ValueError(f"Monthly comparison calculation failed: {e}")

    def filter_sessions_by_period(self, sessions: List[GameSession],
                                  start_date: datetime, end_date: datetime) -> List[GameSession]:
        """
        Filter sessions by date period.

        Args:
            sessions: List of GameSession objects
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (exclusive)

        Returns:
            List[GameSession]: Filtered sessions within the date range
        """
        try:
            filtered_sessions = []

            for session in sessions:
                session_date = session.date
                if start_date.date() <= session_date.date() < end_date.date():
                    filtered_sessions.append(session)

            self.logger.info(
                f"Filtered {len(filtered_sessions)} sessions from {len(sessions)} total sessions")
            return filtered_sessions

        except Exception as e:
            self.logger.error(f"Failed to filter sessions by period: {e}")
            raise ValueError(f"Session filtering failed: {e}")

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction from a list of values.

        Args:
            values: List of numeric values in chronological order

        Returns:
            str: 'increasing', 'decreasing', 'stable', or 'insufficient_data'
        """
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear trend calculation
        increases = 0
        decreases = 0

        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increases += 1
            elif values[i] < values[i-1]:
                decreases += 1

        if increases > decreases:
            return 'increasing'
        elif decreases > increases:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_volatility(self, values: List[float]) -> float:
        """
        Calculate volatility (standard deviation) of values.

        Args:
            values: List of numeric values

        Returns:
            float: Standard deviation of the values
        """
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def calculate_machine_stats(self, sessions: List[GameSession], machine_name: str) -> MachineStats:
        """
        Calculate statistics for a specific machine.

        Args:
            sessions: List of all GameSession objects
            machine_name: Name of the machine to calculate stats for

        Returns:
            MachineStats: Machine-specific statistics
        """
        try:
            # Filter sessions for the specific machine
            machine_sessions = [
                s for s in sessions if s.machine_name == machine_name]

            if not machine_sessions:
                return MachineStats(
                    machine_name=machine_name,
                    basic_stats=self._empty_basic_stats(),
                    store_distribution={},
                    avg_session_duration=None
                )

            # Calculate basic stats for this machine
            basic_stats = self.calculate_basic_stats(machine_sessions)

            # Calculate store distribution
            store_distribution = {}
            for session in machine_sessions:
                store = session.store_name
                store_distribution[store] = store_distribution.get(
                    store, 0) + 1

            # Calculate average session duration
            completed_sessions = [
                s for s in machine_sessions if s.is_completed]
            durations = []

            for session in completed_sessions:
                duration = self._calculate_session_duration(session)
                if duration is not None:
                    durations.append(duration)

            avg_duration = sum(durations) / \
                len(durations) if durations else None

            self.logger.info(
                f"Calculated machine stats for '{machine_name}': {len(machine_sessions)} sessions")

            return MachineStats(
                machine_name=machine_name,
                basic_stats=basic_stats,
                store_distribution=store_distribution,
                avg_session_duration=avg_duration
            )

        except Exception as e:
            self.logger.error(
                f"Failed to calculate machine stats for '{machine_name}': {e}")
            raise ValueError(f"Machine statistics calculation failed: {e}")

    def get_all_machine_stats(self, user_id: str, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[MachineStats]:
        """
        Get statistics for all machines played by a user.

        Args:
            user_id: User ID to calculate stats for
            date_range: Optional date range for filtering sessions

        Returns:
            List[MachineStats]: List of machine statistics sorted by total sessions

        Raises:
            DatabaseError: If database query fails
        """
        try:
            # Get all sessions for the user
            sessions = self.db_manager.get_sessions(user_id, date_range)

            # Get unique machine names
            machine_names = list(set(s.machine_name for s in sessions))

            # Calculate stats for each machine
            machine_stats = []
            for machine_name in machine_names:
                stats = self.calculate_machine_stats(sessions, machine_name)
                machine_stats.append(stats)

            # Sort by total sessions (descending)
            machine_stats.sort(
                key=lambda x: x.basic_stats.total_sessions, reverse=True)

            self.logger.info(
                f"Calculated stats for {len(machine_stats)} machines")
            return machine_stats

        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get all machine stats: {e}")
            raise ValueError(f"All machine statistics calculation failed: {e}")

    def get_machine_performance_ranking(self, user_id: str,
                                        date_range: Optional[Tuple[datetime,
                                                                   datetime]] = None,
                                        min_sessions: int = 3) -> Dict[str, Any]:
        """
        Get machine performance ranking based on various metrics.

        Args:
            user_id: User ID to calculate rankings for
            date_range: Optional date range for filtering sessions
            min_sessions: Minimum number of sessions required for ranking

        Returns:
            Dict containing various machine rankings
        """
        try:
            machine_stats = self.get_all_machine_stats(user_id, date_range)

            # Filter machines with sufficient data
            qualified_machines = [
                m for m in machine_stats
                if m.basic_stats.completed_sessions >= min_sessions
            ]

            if not qualified_machines:
                return {
                    'total_machines': len(machine_stats),
                    'qualified_machines': 0,
                    'min_sessions_required': min_sessions,
                    'rankings': {}
                }

            # Create rankings
            rankings = {
                'by_total_profit': sorted(qualified_machines,
                                          key=lambda x: x.basic_stats.total_profit, reverse=True),
                'by_win_rate': sorted(qualified_machines,
                                      key=lambda x: x.basic_stats.win_rate, reverse=True),
                'by_avg_profit': sorted(qualified_machines,
                                        key=lambda x: x.basic_stats.avg_profit, reverse=True),
                'by_avg_investment': sorted(qualified_machines,
                                            key=lambda x: x.basic_stats.avg_investment, reverse=False),
                'by_session_count': sorted(qualified_machines,
                                           key=lambda x: x.basic_stats.total_sessions, reverse=True)
            }

            # Calculate performance scores (weighted combination of metrics)
            for machine in qualified_machines:
                stats = machine.basic_stats
                # Normalize metrics and calculate composite score
                profit_score = stats.total_profit / 10000  # Normalize by 10k yen
                win_rate_score = stats.win_rate / 100  # Convert percentage to 0-1
                # Lower variance is better
                consistency_score = 1 / (1 + stats.profit_variance / 10000)

                machine.performance_score = (profit_score * 0.4 +
                                             win_rate_score * 0.3 +
                                             consistency_score * 0.3)

            rankings['by_performance_score'] = sorted(qualified_machines,
                                                      key=lambda x: x.performance_score, reverse=True)

            return {
                'total_machines': len(machine_stats),
                'qualified_machines': len(qualified_machines),
                'min_sessions_required': min_sessions,
                'rankings': rankings
            }

        except Exception as e:
            self.logger.error(
                f"Failed to calculate machine performance ranking: {e}")
            raise ValueError(
                f"Machine performance ranking calculation failed: {e}")

    def analyze_machine_performance(self, user_id: str, machine_name: str,
                                    date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Perform detailed performance analysis for a specific machine.

        Args:
            user_id: User ID to analyze for
            machine_name: Name of the machine to analyze
            date_range: Optional date range for filtering sessions

        Returns:
            Dict containing detailed machine analysis
        """
        try:
            # Get sessions for the user and filter by machine
            sessions = self.db_manager.get_sessions(user_id, date_range)
            machine_sessions = [
                s for s in sessions if s.machine_name == machine_name]

            if not machine_sessions:
                return {
                    'machine_name': machine_name,
                    'has_data': False,
                    'message': 'No sessions found for this machine'
                }

            # Calculate machine stats
            machine_stats = self.calculate_machine_stats(
                sessions, machine_name)

            # Analyze session patterns
            completed_sessions = [
                s for s in machine_sessions if s.is_completed]

            # Time-based analysis
            session_times = {}
            for session in completed_sessions:
                hour = session.start_time.hour
                session_times[hour] = session_times.get(hour, [])
                session_times[hour].append(session.profit)

            best_hours = {}
            for hour, profits in session_times.items():
                avg_profit = sum(profits) / len(profits)
                best_hours[hour] = {
                    'avg_profit': avg_profit,
                    'session_count': len(profits),
                    'win_rate': len([p for p in profits if p > 0]) / len(profits) * 100
                }

            # Store performance analysis
            store_performance = {}
            for session in completed_sessions:
                store = session.store_name
                if store not in store_performance:
                    store_performance[store] = []
                store_performance[store].append(session.profit)

            for store, profits in store_performance.items():
                store_performance[store] = {
                    'avg_profit': sum(profits) / len(profits),
                    'session_count': len(profits),
                    'win_rate': len([p for p in profits if p > 0]) / len(profits) * 100,
                    'total_profit': sum(profits)
                }

            # Recent performance trend (last 10 sessions)
            recent_sessions = sorted(
                completed_sessions, key=lambda x: x.date, reverse=True)[:10]
            recent_profits = [s.profit for s in recent_sessions]
            recent_trend = self._calculate_trend(recent_profits)

            return {
                'machine_name': machine_name,
                'has_data': True,
                'machine_stats': machine_stats,
                'time_analysis': {
                    'best_hours': dict(sorted(best_hours.items(),
                                              key=lambda x: x[1]['avg_profit'], reverse=True)),
                    'session_distribution': session_times
                },
                'store_analysis': dict(sorted(store_performance.items(),
                                              key=lambda x: x[1]['avg_profit'], reverse=True)),
                'recent_performance': {
                    'trend': recent_trend,
                    'last_10_sessions': len(recent_sessions),
                    'recent_avg_profit': sum(recent_profits) / len(recent_profits) if recent_profits else 0
                },
                'recommendations': self._generate_machine_recommendations(machine_stats, best_hours, store_performance)
            }

        except Exception as e:
            self.logger.error(
                f"Failed to analyze machine performance for '{machine_name}': {e}")
            raise ValueError(f"Machine performance analysis failed: {e}")

    def _generate_machine_recommendations(self, machine_stats: MachineStats,
                                          best_hours: Dict, store_performance: Dict) -> List[str]:
        """
        Generate recommendations based on machine performance analysis.

        Args:
            machine_stats: Machine statistics
            best_hours: Best performing hours
            store_performance: Store performance data

        Returns:
            List of recommendation strings
        """
        recommendations = []

        try:
            stats = machine_stats.basic_stats

            # Win rate recommendations
            if stats.win_rate > 60:
                recommendations.append("この機種は高い勝率を示しています。継続してプレイすることをお勧めします。")
            elif stats.win_rate < 30:
                recommendations.append("この機種の勝率が低いです。他の機種を検討することをお勧めします。")

            # Profit recommendations
            if stats.avg_profit > 5000:
                recommendations.append("平均収支が良好です。この機種での戦略を維持してください。")
            elif stats.avg_profit < -10000:
                recommendations.append("平均収支が悪化しています。投資額の見直しを検討してください。")

            # Time-based recommendations
            if best_hours:
                best_hour = max(best_hours.items(),
                                key=lambda x: x[1]['avg_profit'])
                if best_hour[1]['avg_profit'] > 0:
                    recommendations.append(f"{best_hour[0]}時台のプレイが最も収益性が高いです。")

            # Store recommendations
            if store_performance and len(store_performance) > 1:
                best_store = max(store_performance.items(),
                                 key=lambda x: x[1]['avg_profit'])
                if best_store[1]['avg_profit'] > 0:
                    recommendations.append(f"{best_store[0]}での成績が最も良好です。")

            # Session count recommendations
            if stats.completed_sessions < 5:
                recommendations.append("データが不十分です。より多くのセッションでの検証をお勧めします。")

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return ["推奨事項の生成中にエラーが発生しました。"]

    def validate_stats_data(self, sessions: List[GameSession]) -> Dict[str, Any]:
        """
        Validate session data for statistics calculation.

        Args:
            sessions: List of GameSession objects to validate

        Returns:
            Dict containing validation results and warnings
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'total_sessions': len(sessions),
            'completed_sessions': 0,
            'incomplete_sessions': 0,
            'invalid_sessions': 0
        }

        try:
            for i, session in enumerate(sessions):
                # Check if session is completed
                if session.is_completed:
                    validation_result['completed_sessions'] += 1

                    # Validate completed session data
                    if session.profit is None:
                        validation_result['errors'].append(
                            f"Session {i}: Completed session missing profit calculation")
                        validation_result['invalid_sessions'] += 1

                    if session.final_investment is None or session.return_amount is None:
                        validation_result['errors'].append(
                            f"Session {i}: Completed session missing investment/return data")
                        validation_result['invalid_sessions'] += 1

                    # Check for logical inconsistencies
                    if session.final_investment and session.initial_investment:
                        if session.final_investment < session.initial_investment:
                            validation_result['warnings'].append(
                                f"Session {i}: Final investment less than initial investment")

                    # Check for extreme values that might indicate data entry errors
                    if session.final_investment and session.final_investment > 1000000:  # 100万円
                        validation_result['warnings'].append(
                            f"Session {i}: Very high investment amount")

                    if session.return_amount and session.return_amount > 10000000:  # 1000万円
                        validation_result['warnings'].append(
                            f"Session {i}: Very high return amount")

                else:
                    validation_result['incomplete_sessions'] += 1

            # Set overall validity
            validation_result['is_valid'] = len(
                validation_result['errors']) == 0

            # Add summary warnings
            if validation_result['incomplete_sessions'] > 0:
                validation_result['warnings'].append(
                    f"{validation_result['incomplete_sessions']} incomplete sessions will be excluded from calculations")

            if validation_result['completed_sessions'] < 5:
                validation_result['warnings'].append(
                    "Limited data available - statistics may not be representative")

            self.logger.info(
                f"Validated {len(sessions)} sessions: {validation_result['completed_sessions']} completed, {validation_result['incomplete_sessions']} incomplete")

            return validation_result

        except Exception as e:
            self.logger.error(f"Stats data validation failed: {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(
                f"Validation process failed: {e}")
            return validation_result

    def generate_basic_stats_charts(self, basic_stats: BasicStats) -> Dict[str, go.Figure]:
        """
        Generate interactive charts for basic statistics.

        Args:
            basic_stats: BasicStats object containing the statistics data

        Returns:
            Dict[str, go.Figure]: Dictionary of chart names to Plotly figures
        """
        try:
            charts = {}

            # 1. Total Profit Chart (Big Number Display)
            profit_color = '#00FF00' if basic_stats.total_profit >= 0 else '#FF4444'
            profit_fig = go.Figure()
            profit_fig.add_trace(go.Indicator(
                mode="number",
                value=basic_stats.total_profit,
                title={"text": "総収支", "font": {
                    "size": 24, "color": "#FFD700"}},
                number={"font": {"size": 48, "color": profit_color}, "suffix": "円"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            profit_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=200,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            charts['total_profit'] = profit_fig

            # 2. Win Rate Gauge Chart
            win_rate_fig = go.Figure()
            win_rate_fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=basic_stats.win_rate,
                title={'text': "勝率", "font": {"size": 24, "color": "#FFD700"}},
                number={"font": {"size": 32, "color": "#00BFFF"}, "suffix": "%"},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': "#FFFFFF"},
                    'bar': {'color': "#00BFFF"},
                    'bgcolor': "rgba(255,255,255,0.1)",
                    'borderwidth': 2,
                    'bordercolor': "#FFD700",
                    'steps': [
                        {'range': [0, 30], 'color': "#FF4444"},
                        {'range': [30, 50], 'color': "#FFA500"},
                        {'range': [50, 70], 'color': "#FFFF00"},
                        {'range': [70, 100], 'color': "#00FF00"}
                    ],
                    'threshold': {
                        'line': {'color': "#FFD700", 'width': 4},
                        'thickness': 0.75,
                        'value': 50
                    }
                },
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            win_rate_fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#FFFFFF"},
                height=300,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            charts['win_rate'] = win_rate_fig

            # 3. Session Summary Bar Chart
            session_data = {
                'カテゴリ': ['勝ちセッション', '負けセッション', '未完了セッション'],
                '回数': [
                    basic_stats.winning_sessions,
                    basic_stats.losing_sessions,
                    basic_stats.total_sessions - basic_stats.completed_sessions
                ],
                'colors': ['#00FF00', '#FF4444', '#8A2BE2']
            }

            session_fig = go.Figure()
            session_fig.add_trace(go.Bar(
                x=session_data['カテゴリ'],
                y=session_data['回数'],
                marker_color=session_data['colors'],
                text=session_data['回数'],
                textposition='auto',
                textfont=dict(size=16, color='white'),
                hovertemplate='<b>%{x}</b><br>回数: %{y}<extra></extra>'
            ))

            session_fig.update_layout(
                title={
                    'text': 'セッション内訳',
                    'x': 0.5,
                    'font': {'size': 20, 'color': '#FFD700'}
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#FFFFFF"},
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF')
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF')
                ),
                height=400,
                margin=dict(l=50, r=50, t=80, b=50)
            )
            charts['session_summary'] = session_fig

            # 4. Average Values Comparison Chart
            avg_data = {
                '指標': ['平均投資額', '平均回収額', '平均収支'],
                '金額': [
                    basic_stats.avg_investment,
                    basic_stats.avg_return,
                    basic_stats.avg_profit
                ],
                'colors': ['#8A2BE2', '#00BFFF', '#00FF00' if basic_stats.avg_profit >= 0 else '#FF4444']
            }

            avg_fig = go.Figure()
            avg_fig.add_trace(go.Bar(
                x=avg_data['指標'],
                y=avg_data['金額'],
                marker_color=avg_data['colors'],
                text=[f'{val:,.0f}円' for val in avg_data['金額']],
                textposition='auto',
                textfont=dict(size=14, color='white'),
                hovertemplate='<b>%{x}</b><br>金額: %{y:,.0f}円<extra></extra>'
            ))

            avg_fig.update_layout(
                title={
                    'text': '平均値比較',
                    'x': 0.5,
                    'font': {'size': 20, 'color': '#FFD700'}
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#FFFFFF"},
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF')
                ),
                yaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF'),
                    title='金額（円）'
                ),
                height=400,
                margin=dict(l=50, r=50, t=80, b=50)
            )
            charts['averages'] = avg_fig

            # 5. Profit Range Distribution (if we have enough data)
            if basic_stats.completed_sessions > 0:
                profit_range_fig = go.Figure()

                # Create profit range indicators
                profit_indicators = [
                    {'label': '最高収支', 'value': basic_stats.max_profit,
                        'color': '#00FF00'},
                    {'label': '平均収支', 'value': basic_stats.avg_profit,
                        'color': '#00BFFF'},
                    {'label': '最低収支', 'value': basic_stats.min_profit,
                        'color': '#FF4444'}
                ]

                for i, indicator in enumerate(profit_indicators):
                    profit_range_fig.add_trace(go.Bar(
                        x=[indicator['label']],
                        y=[indicator['value']],
                        name=indicator['label'],
                        marker_color=indicator['color'],
                        text=f"{indicator['value']:+,.0f}円",
                        textposition='auto',
                        textfont=dict(size=14, color='white'),
                        hovertemplate=f'<b>{indicator["label"]}</b><br>金額: %{{y:+,.0f}}円<extra></extra>',
                        showlegend=False
                    ))

                profit_range_fig.update_layout(
                    title={
                        'text': '収支レンジ',
                        'x': 0.5,
                        'font': {'size': 20, 'color': '#FFD700'}
                    },
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': "#FFFFFF"},
                    xaxis=dict(
                        gridcolor='rgba(255,255,255,0.2)',
                        tickfont=dict(color='#FFFFFF')
                    ),
                    yaxis=dict(
                        gridcolor='rgba(255,255,255,0.2)',
                        tickfont=dict(color='#FFFFFF'),
                        title='金額（円）'
                    ),
                    height=400,
                    margin=dict(l=50, r=50, t=80, b=50)
                )
                charts['profit_range'] = profit_range_fig

            self.logger.info(
                f"Generated {len(charts)} basic statistics charts")
            return charts

        except Exception as e:
            self.logger.error(f"Failed to generate basic stats charts: {e}")
            raise ValueError(f"Chart generation failed: {e}")

    def generate_monthly_stats_chart(self, monthly_stats_list: List[MonthlyStats]) -> go.Figure:
        """
        Generate monthly statistics chart.

        Args:
            monthly_stats_list: List of MonthlyStats objects

        Returns:
            go.Figure: Plotly figure for monthly statistics
        """
        try:
            if not monthly_stats_list:
                # Return empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="データがありません",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=20, color="#FFFFFF")
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                return fig

            # Prepare data
            months = [
                f"{stats.year}/{stats.month:02d}" for stats in monthly_stats_list]
            profits = [
                stats.basic_stats.total_profit for stats in monthly_stats_list]
            win_rates = [
                stats.basic_stats.win_rate for stats in monthly_stats_list]
            sessions = [
                stats.basic_stats.completed_sessions for stats in monthly_stats_list]

            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=1, cols=1,
                specs=[[{"secondary_y": True}]],
                subplot_titles=["月別収支・勝率推移"]
            )

            # Add profit bar chart
            fig.add_trace(
                go.Bar(
                    x=months,
                    y=profits,
                    name='収支',
                    marker_color=['#00FF00' if p >=
                                  0 else '#FF4444' for p in profits],
                    text=[f'{p:+,.0f}円' for p in profits],
                    textposition='auto',
                    textfont=dict(size=12, color='white'),
                    hovertemplate='<b>%{x}</b><br>収支: %{y:+,.0f}円<extra></extra>',
                    yaxis='y'
                ),
                secondary_y=False
            )

            # Add win rate line chart
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=win_rates,
                    mode='lines+markers',
                    name='勝率',
                    line=dict(color='#FFD700', width=3),
                    marker=dict(size=8, color='#FFD700'),
                    text=[f'{wr:.1f}%' for wr in win_rates],
                    textposition='top center',
                    textfont=dict(size=10, color='#FFD700'),
                    hovertemplate='<b>%{x}</b><br>勝率: %{y:.1f}%<extra></extra>',
                    yaxis='y2'
                ),
                secondary_y=True
            )

            # Update layout
            fig.update_layout(
                title={
                    'text': '月別統計',
                    'x': 0.5,
                    'font': {'size': 24, 'color': '#FFD700'}
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#FFFFFF"},
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF'),
                    title='月'
                ),
                height=500,
                margin=dict(l=50, r=50, t=100, b=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='#FFFFFF')
                )
            )

            # Update y-axes
            fig.update_yaxes(
                title_text="収支（円）",
                gridcolor='rgba(255,255,255,0.2)',
                tickfont=dict(color='#FFFFFF'),
                secondary_y=False
            )
            fig.update_yaxes(
                title_text="勝率（%）",
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='#FFFFFF'),
                secondary_y=True
            )

            self.logger.info(
                f"Generated monthly stats chart for {len(monthly_stats_list)} months")
            return fig

        except Exception as e:
            self.logger.error(f"Failed to generate monthly stats chart: {e}")
            raise ValueError(f"Monthly chart generation failed: {e}")

    def generate_machine_stats_chart(self, machine_stats_list: List[MachineStats], min_sessions: int = 3) -> go.Figure:
        """
        Generate machine statistics chart.

        Args:
            machine_stats_list: List of MachineStats objects
            min_sessions: Minimum sessions required to include machine in chart

        Returns:
            go.Figure: Plotly figure for machine statistics
        """
        try:
            if not machine_stats_list:
                # Return empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="データがありません",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=20, color="#FFFFFF")
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                return fig

            # Filter machines with sufficient data
            qualified_machines = [
                m for m in machine_stats_list
                if m.basic_stats.completed_sessions >= min_sessions
            ]

            if not qualified_machines:
                # Return chart with insufficient data message
                fig = go.Figure()
                fig.add_annotation(
                    text=f"十分なデータがありません<br>（最低{min_sessions}セッション必要）",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="#FFFFFF")
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                return fig

            # Sort by total profit (descending)
            qualified_machines.sort(
                key=lambda x: x.basic_stats.total_profit, reverse=True)

            # Prepare data (limit to top 10 machines for readability)
            top_machines = qualified_machines[:10]
            machine_names = [m.machine_name[:20] + '...' if len(m.machine_name) > 20 else m.machine_name
                             for m in top_machines]
            profits = [m.basic_stats.total_profit for m in top_machines]
            win_rates = [m.basic_stats.win_rate for m in top_machines]
            sessions = [m.basic_stats.completed_sessions for m in top_machines]

            # Create subplot with secondary y-axis
            fig = make_subplots(
                rows=1, cols=1,
                specs=[[{"secondary_y": True}]],
                subplot_titles=["機種別収支・勝率"]
            )

            # Add profit bar chart
            fig.add_trace(
                go.Bar(
                    x=machine_names,
                    y=profits,
                    name='総収支',
                    marker_color=['#00FF00' if p >=
                                  0 else '#FF4444' for p in profits],
                    text=[f'{p:+,.0f}円' for p in profits],
                    textposition='auto',
                    textfont=dict(size=10, color='white'),
                    hovertemplate='<b>%{x}</b><br>総収支: %{y:+,.0f}円<br>セッション数: ' +
                                 '<br>'.join(
                                     [f'{s}回' for s in sessions]) + '<extra></extra>',
                    yaxis='y'
                ),
                secondary_y=False
            )

            # Add win rate line chart
            fig.add_trace(
                go.Scatter(
                    x=machine_names,
                    y=win_rates,
                    mode='lines+markers',
                    name='勝率',
                    line=dict(color='#FFD700', width=3),
                    marker=dict(size=8, color='#FFD700'),
                    text=[f'{wr:.1f}%' for wr in win_rates],
                    textposition='top center',
                    textfont=dict(size=9, color='#FFD700'),
                    hovertemplate='<b>%{x}</b><br>勝率: %{y:.1f}%<extra></extra>',
                    yaxis='y2'
                ),
                secondary_y=True
            )

            # Update layout
            fig.update_layout(
                title={
                    'text': '機種別統計（上位10機種）',
                    'x': 0.5,
                    'font': {'size': 20, 'color': '#FFD700'}
                },
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': "#FFFFFF"},
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.2)',
                    tickfont=dict(color='#FFFFFF', size=10),
                    title='機種名',
                    tickangle=45
                ),
                height=600,
                margin=dict(l=50, r=50, t=100, b=150),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color='#FFFFFF')
                )
            )

            # Update y-axes
            fig.update_yaxes(
                title_text="総収支（円）",
                gridcolor='rgba(255,255,255,0.2)',
                tickfont=dict(color='#FFFFFF'),
                secondary_y=False
            )
            fig.update_yaxes(
                title_text="勝率（%）",
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='#FFFFFF'),
                secondary_y=True
            )

            self.logger.info(
                f"Generated machine stats chart for {len(top_machines)} machines")
            return fig

        except Exception as e:
            self.logger.error(f"Failed to generate machine stats chart: {e}")
            raise ValueError(f"Machine chart generation failed: {e}")
