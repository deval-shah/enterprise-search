import time
import asyncio
from contextlib import contextmanager, asynccontextmanager
import threading
from tabulate import tabulate
import statistics
from llamasearch.settings import config
from llamasearch.logger import logger

class LatencyTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LatencyTracker, cls).__new__(cls)
                    cls._instance.latencies = {}
                    if config.application.enable_prometheus:
                        from prometheus_client import Summary, start_http_server
                        cls._instance.prometheus_summary = Summary('method_latency', 'Latency of pipeline calls', ['method'])
                        start_http_server(8000)  # Start Prometheus metrics server
        return cls._instance

    @contextmanager
    def track(self, method_name):
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            latency = end_time - start_time
            self.record_latency(method_name, latency)

    @asynccontextmanager
    async def track_async(self, method_name):
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            latency = end_time - start_time
            self.record_latency(method_name, latency)

    def record_latency(self, method_name, latency):
        self.latencies[method_name] = latency
        if config.application.enable_prometheus:
            self.prometheus_summary.labels(method=method_name).observe(latency)

    def get_latency(self, method_name):
        return self.latencies.get(method_name)

    def print_summary(self):
        headers = ["Method", "Latency (seconds)"]
        table_data = [[method, f"{latency:.4f}"] for method, latency in self.latencies.items()]
        logger.info("\nLatency Summary:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def report_stats(self):
        if not self.latencies:
            logger.info("No latency data available.")
            return
        latencies = list(self.latencies.values())
        stats = {
            "Total Methods": len(latencies),
            "Total Time": f"{sum(latencies):.4f}s",
            "Average": f"{statistics.mean(latencies):.4f}s",
            "Median": f"{statistics.median(latencies):.4f}s",
            "Min": f"{min(latencies):.4f}s",
            "Max": f"{max(latencies):.4f}s",
            "Standard Deviation": f"{statistics.stdev(latencies):.4f}s" if len(latencies) > 1 else "N/A"
        }
        headers = ["Statistic", "Value"]
        table_data = [[stat, value] for stat, value in stats.items()]
        logger.info("\nLatency Statistics:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

def track_latency(func):
    tracker = LatencyTracker()    
    if asyncio.iscoroutinefunction(func):
        async def wrapper(*args, **kwargs):
            async with tracker.track_async(func.__name__):
                return await func(*args, **kwargs)
    else:
        def wrapper(*args, **kwargs):
            with tracker.track(func.__name__):
                return func(*args, **kwargs)
    
    return wrapper
