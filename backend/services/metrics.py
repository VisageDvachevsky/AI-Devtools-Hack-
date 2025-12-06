"""
Prometheus Metrics and Real-Time Monitoring
Tracks system performance, API usage, and candidate analysis metrics
"""
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MetricType:
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric(BaseModel):
    name: str
    metric_type: str
    help_text: str
    value: float = 0.0
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class PrometheusMetrics:
    """
    Prometheus-compatible metrics collector
    Exposes metrics in Prometheus format for scraping
    """

    def __init__(self):
        # Metrics storage
        self.metrics: Dict[str, Metric] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Initialize common metrics
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize standard HR system metrics"""

        # API metrics
        self.register_counter(
            "hr_api_requests_total",
            "Total number of API requests"
        )
        self.register_counter(
            "hr_api_errors_total",
            "Total number of API errors"
        )
        self.register_histogram(
            "hr_api_request_duration_seconds",
            "API request duration in seconds"
        )

        # Candidate analysis metrics
        self.register_counter(
            "hr_candidates_analyzed_total",
            "Total number of candidates analyzed"
        )
        self.register_counter(
            "hr_candidates_accepted_total",
            "Number of candidates marked as 'go'"
        )
        self.register_counter(
            "hr_candidates_rejected_total",
            "Number of candidates rejected"
        )

        # GitHub analysis metrics
        self.register_counter(
            "hr_github_api_calls_total",
            "Total GitHub API calls made"
        )
        self.register_counter(
            "hr_github_rate_limits_total",
            "Number of times GitHub rate limit was hit"
        )
        self.register_histogram(
            "hr_github_analysis_duration_seconds",
            "GitHub analysis duration"
        )

        # Cache metrics
        self.register_counter(
            "hr_cache_hits_total",
            "Total cache hits"
        )
        self.register_counter(
            "hr_cache_misses_total",
            "Total cache misses"
        )
        self.register_gauge(
            "hr_cache_hit_rate",
            "Current cache hit rate percentage"
        )

        # Batch processing metrics
        self.register_gauge(
            "hr_batch_jobs_active",
            "Number of active batch jobs"
        )
        self.register_counter(
            "hr_batch_jobs_completed_total",
            "Total completed batch jobs"
        )
        self.register_histogram(
            "hr_batch_job_duration_seconds",
            "Batch job processing duration"
        )

        # Market analytics metrics
        self.register_counter(
            "hr_market_data_fetches_total",
            "Total market data fetches from HH.ru"
        )
        self.register_histogram(
            "hr_market_data_fetch_duration_seconds",
            "Market data fetch duration"
        )

        # Scoring metrics
        self.register_histogram(
            "hr_candidate_scores",
            "Distribution of candidate scores"
        )
        self.register_gauge(
            "hr_average_candidate_score",
            "Average candidate score"
        )

    def register_counter(self, name: str, help_text: str):
        """Register a counter metric"""
        self.metrics[name] = Metric(
            name=name,
            metric_type=MetricType.COUNTER,
            help_text=help_text,
            value=0.0
        )

    def register_gauge(self, name: str, help_text: str):
        """Register a gauge metric"""
        self.metrics[name] = Metric(
            name=name,
            metric_type=MetricType.GAUGE,
            help_text=help_text,
            value=0.0
        )

    def register_histogram(self, name: str, help_text: str):
        """Register a histogram metric"""
        self.metrics[name] = Metric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            help_text=help_text
        )

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        key = self._build_metric_key(name, labels)
        self.counters[key] += value

        if name in self.metrics:
            self.metrics[name].value += value
            self.metrics[name].timestamp = time.time()

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        key = self._build_metric_key(name, labels)
        self.gauges[key] = value

        if name in self.metrics:
            self.metrics[name].value = value
            self.metrics[name].timestamp = time.time()

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram observation"""
        key = self._build_metric_key(name, labels)
        self.histograms[key].append(value)

        # Update metric
        if name in self.metrics:
            self.metrics[name].timestamp = time.time()

    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Build metric key with labels"""
        if not labels:
            return name

        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a specific metric"""
        return self.metrics.get(name)

    def export_prometheus_format(self) -> str:
        """
        Export all metrics in Prometheus text format
        Compatible with Prometheus scraping
        """
        lines = []

        # Export counters
        for key, value in self.counters.items():
            metric_name = key.split("{")[0]
            metric = self.metrics.get(metric_name)

            if metric:
                lines.append(f"# HELP {metric_name} {metric.help_text}")
                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{key} {value}")

        # Export gauges
        for key, value in self.gauges.items():
            metric_name = key.split("{")[0]
            metric = self.metrics.get(metric_name)

            if metric:
                lines.append(f"# HELP {metric_name} {metric.help_text}")
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{key} {value}")

        # Export histograms (simplified - sum and count)
        for key, values in self.histograms.items():
            if not values:
                continue

            metric_name = key.split("{")[0]
            metric = self.metrics.get(metric_name)

            if metric:
                lines.append(f"# HELP {metric_name} {metric.help_text}")
                lines.append(f"# TYPE {metric_name} histogram")

                # Sum and count
                total = sum(values)
                count = len(values)

                lines.append(f"{key}_sum {total}")
                lines.append(f"{key}_count {count}")

                # Buckets (simplified)
                buckets = [0.1, 0.5, 1.0, 5.0, 10.0, float('inf')]
                for bucket in buckets:
                    count_in_bucket = sum(1 for v in values if v <= bucket)
                    lines.append(f'{key}_bucket{{le="{bucket}"}} {count_in_bucket}')

        return "\n".join(lines)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics for dashboard"""
        stats = {}

        # Calculate cache hit rate
        cache_hits = self.counters.get("hr_cache_hits_total", 0)
        cache_misses = self.counters.get("hr_cache_misses_total", 0)
        total_cache_requests = cache_hits + cache_misses

        if total_cache_requests > 0:
            cache_hit_rate = (cache_hits / total_cache_requests) * 100
            self.set_gauge("hr_cache_hit_rate", cache_hit_rate)
            stats["cache_hit_rate"] = round(cache_hit_rate, 2)

        # Calculate average candidate score
        candidate_scores = self.histograms.get("hr_candidate_scores", [])
        if candidate_scores:
            avg_score = sum(candidate_scores) / len(candidate_scores)
            self.set_gauge("hr_average_candidate_score", avg_score)
            stats["average_candidate_score"] = round(avg_score, 2)

        # General stats
        stats["total_candidates_analyzed"] = self.counters.get("hr_candidates_analyzed_total", 0)
        stats["candidates_accepted"] = self.counters.get("hr_candidates_accepted_total", 0)
        stats["candidates_rejected"] = self.counters.get("hr_candidates_rejected_total", 0)
        stats["total_api_requests"] = self.counters.get("hr_api_requests_total", 0)
        stats["total_api_errors"] = self.counters.get("hr_api_errors_total", 0)

        # Acceptance rate
        total_decisions = stats["candidates_accepted"] + stats["candidates_rejected"]
        if total_decisions > 0:
            stats["acceptance_rate"] = round(
                (stats["candidates_accepted"] / total_decisions) * 100, 2
            )

        return stats


# Global metrics instance
metrics = PrometheusMetrics()


class PerformanceMonitor:
    """Context manager for monitoring performance"""

    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metrics.observe_histogram(self.metric_name, duration, self.labels)


def track_api_request(endpoint: str):
    """Decorator to track API requests"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            metrics.inc_counter("hr_api_requests_total", labels={"endpoint": endpoint})

            with PerformanceMonitor("hr_api_request_duration_seconds", {"endpoint": endpoint}):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    metrics.inc_counter("hr_api_errors_total", labels={"endpoint": endpoint})
                    raise

        return wrapper

    return decorator
