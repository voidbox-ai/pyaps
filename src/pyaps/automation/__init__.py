# src/pyaps/automation/__init__.py
from .client import AutomationClient, AutomationError, DEFAULT_AUTOMATION_SCOPES
from .types import WorkItemArgument, WorkItemSpec, AppBundleSpec, ActivitySpec

__all__ = [
    "AutomationClient",
    "AutomationError",
    "DEFAULT_AUTOMATION_SCOPES",
    "WorkItemArgument",
    "WorkItemSpec",
    "AppBundleSpec",
    "ActivitySpec",
]
