"""Logging and tracing utilities for the agent."""

from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from typing import Iterator, Sequence, Union

import structlog
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from pythonjsonlogger import jsonlogger


AttributeValue = Union[
    str, bool, int, float, Sequence[str], Sequence[bool], Sequence[int], Sequence[float]
]


def configure_logging() -> None:
    """Configure structured logging for the application."""

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[handler])
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


def configure_tracing(service_name: str = "todo-agent") -> None:
    """Configure a basic OpenTelemetry tracer with stdout export."""

    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


@contextmanager
def traced_span(name: str, **attributes: AttributeValue) -> Iterator[trace.Span]:
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        start_time = time.perf_counter()
        try:
            yield span
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000
            span.set_attribute("latency_ms", latency_ms)


def emit_metric(metric_name: str, value: float, **labels: str) -> None:
    """Stub for pushing metrics to Cloud Monitoring."""

    logger = get_logger("metrics")
    logger.info("metric_emit", metric_name=metric_name, value=value, labels=labels)
