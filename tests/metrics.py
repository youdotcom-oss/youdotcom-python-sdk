"""
Performance metrics calculation and reporting utilities.

This module provides statistical analysis and pretty-printing for performance test results.
"""

from __future__ import annotations
import statistics
from dataclasses import dataclass
from typing import List, Optional
from tests.timing_client import SDKCallTiming


@dataclass
class PerformanceMetrics:
    """Statistical metrics for a collection of SDK call timings."""
    
    endpoint_name: str
    iterations: int
    
    # SDK total time metrics (in milliseconds)
    sdk_min_ms: float
    sdk_max_ms: float
    sdk_mean_ms: float
    sdk_median_ms: float
    sdk_p95_ms: float
    sdk_p99_ms: float
    sdk_stddev_ms: float
    
    # HTTP time metrics (in milliseconds)
    http_min_ms: float
    http_max_ms: float
    http_mean_ms: float
    http_median_ms: float
    http_p95_ms: float
    http_p99_ms: float
    http_stddev_ms: float
    
    # Overhead metrics (in milliseconds)
    overhead_min_ms: float
    overhead_max_ms: float
    overhead_mean_ms: float
    overhead_median_ms: float
    overhead_p95_ms: float
    overhead_p99_ms: float
    overhead_mean_percentage: float
    
    # Additional info
    success_count: int
    failure_count: int


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile of a dataset."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    weight = index - lower
    
    if upper >= len(sorted_data):
        return sorted_data[lower]
    
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def calculate_metrics(endpoint_name: str, timings: List[SDKCallTiming]) -> PerformanceMetrics:
    """Calculate performance metrics from a list of SDK call timings."""
    if not timings:
        raise ValueError("Cannot calculate metrics from empty timings list")
    
    # Extract timing data
    sdk_times = [t.sdk_duration_ms for t in timings]
    http_times = [t.request_timing.http_duration_ms for t in timings]
    overheads = [t.overhead_ms for t in timings]
    overhead_percentages = [t.overhead_percentage for t in timings]
    
    # Count successes/failures (assuming 2xx is success)
    success_count = sum(1 for t in timings if 200 <= t.request_timing.status_code < 300)
    failure_count = len(timings) - success_count
    
    return PerformanceMetrics(
        endpoint_name=endpoint_name,
        iterations=len(timings),
        
        # SDK metrics
        sdk_min_ms=min(sdk_times),
        sdk_max_ms=max(sdk_times),
        sdk_mean_ms=statistics.mean(sdk_times),
        sdk_median_ms=statistics.median(sdk_times),
        sdk_p95_ms=calculate_percentile(sdk_times, 95),
        sdk_p99_ms=calculate_percentile(sdk_times, 99),
        sdk_stddev_ms=statistics.stdev(sdk_times) if len(sdk_times) > 1 else 0.0,
        
        # HTTP metrics
        http_min_ms=min(http_times),
        http_max_ms=max(http_times),
        http_mean_ms=statistics.mean(http_times),
        http_median_ms=statistics.median(http_times),
        http_p95_ms=calculate_percentile(http_times, 95),
        http_p99_ms=calculate_percentile(http_times, 99),
        http_stddev_ms=statistics.stdev(http_times) if len(http_times) > 1 else 0.0,
        
        # Overhead metrics
        overhead_min_ms=min(overheads),
        overhead_max_ms=max(overheads),
        overhead_mean_ms=statistics.mean(overheads),
        overhead_median_ms=statistics.median(overheads),
        overhead_p95_ms=calculate_percentile(overheads, 95),
        overhead_p99_ms=calculate_percentile(overheads, 99),
        overhead_mean_percentage=statistics.mean(overhead_percentages),
        
        success_count=success_count,
        failure_count=failure_count,
    )


def format_time(ms: float) -> str:
    """Format time in milliseconds to human-readable string."""
    if ms < 1:
        return f"{ms * 1000:.2f}µs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    else:
        return f"{ms / 1000:.2f}s"


def print_metrics_table(metrics_list: List[PerformanceMetrics], title: str = "Performance Test Results") -> None:
    """Print a formatted table of performance metrics."""
    if not metrics_list:
        print("No metrics to display")
        return
    
    print(f"\n{'=' * 120}")
    print(f"{title:^120}")
    print(f"{'=' * 120}\n")
    
    # Header
    print(f"{'Endpoint':<50} {'P50':>10} {'P95':>10} {'P99':>10} {'Mean':>10} {'Overhead':>10} {'%':>6}")
    print(f"{'-' * 50} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 10} {'-' * 6}")
    
    # Data rows
    for m in metrics_list:
        print(
            f"{m.endpoint_name:<50} "
            f"{format_time(m.sdk_median_ms):>10} "
            f"{format_time(m.sdk_p95_ms):>10} "
            f"{format_time(m.sdk_p99_ms):>10} "
            f"{format_time(m.sdk_mean_ms):>10} "
            f"{format_time(m.overhead_mean_ms):>10} "
            f"{m.overhead_mean_percentage:>5.1f}%"
        )
    
    print(f"{'-' * 120}\n")
    
    # Summary statistics
    all_overheads = [m.overhead_mean_ms for m in metrics_list]
    all_percentages = [m.overhead_mean_percentage for m in metrics_list]
    total_iterations = sum(m.iterations for m in metrics_list)
    total_successes = sum(m.success_count for m in metrics_list)
    total_failures = sum(m.failure_count for m in metrics_list)
    
    print("Summary:")
    print(f"  Total test cases: {len(metrics_list)}")
    print(f"  Total iterations: {total_iterations}")
    print(f"  Success rate: {total_successes}/{total_iterations} ({100 * total_successes / total_iterations:.1f}%)")
    if total_failures > 0:
        print(f"  Failures: {total_failures}")
    print(f"\nSDK Overhead Analysis:")
    print(f"  Average overhead: {format_time(statistics.mean(all_overheads))} ({statistics.mean(all_percentages):.1f}%)")
    print(f"  Min overhead: {format_time(min(all_overheads))} (best case)")
    print(f"  Max overhead: {format_time(max(all_overheads))} (worst case)")
    print(f"  Median overhead: {format_time(statistics.median(all_overheads))}")
    print()


def print_detailed_metrics(metrics: PerformanceMetrics) -> None:
    """Print detailed metrics for a single endpoint."""
    print(f"\n{'=' * 80}")
    print(f"Detailed Metrics: {metrics.endpoint_name}")
    print(f"{'=' * 80}\n")
    
    print(f"Iterations: {metrics.iterations}")
    print(f"Success rate: {metrics.success_count}/{metrics.iterations} ({100 * metrics.success_count / metrics.iterations:.1f}%)")
    if metrics.failure_count > 0:
        print(f"Failures: {metrics.failure_count}")
    
    print(f"\nSDK Total Time:")
    print(f"  Min:    {format_time(metrics.sdk_min_ms)}")
    print(f"  Max:    {format_time(metrics.sdk_max_ms)}")
    print(f"  Mean:   {format_time(metrics.sdk_mean_ms)}")
    print(f"  Median: {format_time(metrics.sdk_median_ms)}")
    print(f"  P95:    {format_time(metrics.sdk_p95_ms)}")
    print(f"  P99:    {format_time(metrics.sdk_p99_ms)}")
    print(f"  StdDev: {format_time(metrics.sdk_stddev_ms)}")
    
    print(f"\nHTTP Time:")
    print(f"  Min:    {format_time(metrics.http_min_ms)}")
    print(f"  Max:    {format_time(metrics.http_max_ms)}")
    print(f"  Mean:   {format_time(metrics.http_mean_ms)}")
    print(f"  Median: {format_time(metrics.http_median_ms)}")
    print(f"  P95:    {format_time(metrics.http_p95_ms)}")
    print(f"  P99:    {format_time(metrics.http_p99_ms)}")
    print(f"  StdDev: {format_time(metrics.http_stddev_ms)}")
    
    print(f"\nSDK Overhead:")
    print(f"  Min:    {format_time(metrics.overhead_min_ms)}")
    print(f"  Max:    {format_time(metrics.overhead_max_ms)}")
    print(f"  Mean:   {format_time(metrics.overhead_mean_ms)} ({metrics.overhead_mean_percentage:.1f}%)")
    print(f"  Median: {format_time(metrics.overhead_median_ms)}")
    print(f"  P95:    {format_time(metrics.overhead_p95_ms)}")
    print(f"  P99:    {format_time(metrics.overhead_p99_ms)}")
    print()


def export_metrics_csv(metrics_list: List[PerformanceMetrics], filename: str) -> None:
    """Export metrics to CSV file."""
    import csv
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'endpoint', 'iterations', 'success_count', 'failure_count',
            'sdk_min_ms', 'sdk_max_ms', 'sdk_mean_ms', 'sdk_median_ms', 'sdk_p95_ms', 'sdk_p99_ms', 'sdk_stddev_ms',
            'http_min_ms', 'http_max_ms', 'http_mean_ms', 'http_median_ms', 'http_p95_ms', 'http_p99_ms', 'http_stddev_ms',
            'overhead_min_ms', 'overhead_max_ms', 'overhead_mean_ms', 'overhead_median_ms', 
            'overhead_p95_ms', 'overhead_p99_ms', 'overhead_mean_percentage'
        ])
        
        # Data rows
        for m in metrics_list:
            writer.writerow([
                m.endpoint_name, m.iterations, m.success_count, m.failure_count,
                m.sdk_min_ms, m.sdk_max_ms, m.sdk_mean_ms, m.sdk_median_ms, m.sdk_p95_ms, m.sdk_p99_ms, m.sdk_stddev_ms,
                m.http_min_ms, m.http_max_ms, m.http_mean_ms, m.http_median_ms, m.http_p95_ms, m.http_p99_ms, m.http_stddev_ms,
                m.overhead_min_ms, m.overhead_max_ms, m.overhead_mean_ms, m.overhead_median_ms,
                m.overhead_p95_ms, m.overhead_p99_ms, m.overhead_mean_percentage
            ])
    
    print(f"Metrics exported to {filename}")
