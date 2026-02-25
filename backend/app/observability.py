"""Azure Application Insights observability via OpenTelemetry.

Uses Microsoft Agent Framework's built-in OpenTelemetry support
(Option 1 — explicit Azure Monitor setup) to export traces, metrics,
and logs to Application Insights.

Reference:
  https://learn.microsoft.com/en-us/agent-framework/agents/observability
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)


def setup_observability() -> None:
    """Configure Azure Monitor OpenTelemetry and enable MAF instrumentation.

    Must be called BEFORE the FastAPI app is created and before any agents
    are instantiated so that all downstream spans are captured.

    If APPLICATION_INSIGHTS_CONNECTION_STRING is not set, observability
    is silently skipped so the app can still run locally without App Insights.
    """
    connection_string = settings.APPLICATION_INSIGHTS_CONNECTION_STRING
    if not connection_string:
        logger.info(
            "APPLICATION_INSIGHTS_CONNECTION_STRING not set — "
            "observability disabled"
        )
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from agent_framework.observability import (
            create_resource,
            enable_instrumentation,
        )

        configure_azure_monitor(
            connection_string=connection_string,
            resource=create_resource(),
            enable_live_metrics=True,
        )

        enable_instrumentation(enable_sensitive_data=False)

        logger.info("Azure Application Insights observability enabled")
    except ImportError as exc:
        logger.warning(
            "Observability packages not installed — skipping: %s", exc
        )
    except Exception as exc:
        logger.warning(
            "Failed to configure observability — skipping: %s", exc
        )
