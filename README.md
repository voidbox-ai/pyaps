# py-aps

Python SDK for Autodesk Platform Service APIs

## Installation

```bash
pip install py-aps
```

## Overview

py-aps is a Python SDK that provides a simple and intuitive interface for interacting with Autodesk Platform Services (formerly known as Forge) APIs. This SDK simplifies authentication, data management, and automation workflows for APS-powered applications.

## Features

- **Authentication**: Easy OAuth2 authentication flow
- **Data Management**: Access and manage files in BIM 360, ACC, and other Autodesk cloud storage
- **Automation**: High-level workflow API for executing WorkItems with automatic file management and webhook support

## Quick Start

### Authentication
```python
from pyaps.auth import AuthClient, Scopes

# 2-legged OAuth
client = AuthClient(client_id="...", client_secret="...")
token = client.two_legged.get_token([Scopes.DATA_READ])
```

### Data Management
```python
from pyaps.datamanagement import DataManagementClient

dm = DataManagementClient(token_provider=lambda: token.access_token)

# List hubs and projects
hubs = list(dm.hubs.list())
projects = list(dm.hubs.list_projects(hub_id))

# Browse folders
contents = list(dm.folders.contents(project_id, folder_id))
```

### Automation (High-Level Workflow)
```python
from pyaps.automation import AutomationWorkflow

workflow = AutomationWorkflow(
    automation_client=auto_client,
    data_client=dm_client,
    default_bucket="my-bucket",
)

# Execute WorkItem with automatic file management
result = workflow.run_workitem_with_files(
    activity_id="Owner.MyActivity+prod",
    input_files={"inputFile": "path/to/input.rvt"},
    output_files={"outputFile": "output.rvt"},
)

# With webhooks (no polling required)
result = workflow.run_workitem_with_files(
    activity_id="Owner.MyActivity+prod",
    input_files={"inputFile": "input.rvt"},
    output_files={"outputFile": "output.rvt"},
    on_complete_url="https://myapp.com/webhook/complete",
)
```

### Automation (Low-Level API)
```python
from pyaps.automation import AutomationClient

auto = AutomationClient(token_provider=lambda: token.access_token)

# List engines
engines = auto.list_engines()

# Start workitem (manual setup required)
workitem = auto.start_workitem({
    'activityId': 'Owner.MyActivity+prod',
    'arguments': {...}
})
```

For more examples and detailed documentation:
- **AutomationWorkflow Guide**: `src/pyaps/automation/WORKFLOW.md`
- **Workflow Examples**: `src/pyaps/automation/workflow_example.py`
- **Low-Level Examples**: `src/pyaps/automation/example.py`
- **Auth Examples**: `src/pyaps/auth/example.py`
- **Data Management Examples**: `src/pyaps/datamanagement/example.py`

## Project Status

**Current version: v0.0.5** - High-level Automation Workflow API added

This package is currently in early development. Active development is underway by **voidbox**.

<details>
<summary><b>Version History</b></summary>

- **v0.0.5** - Added AutomationWorkflow high-level API with automatic file management, webhook support (onComplete/onProgress), batch processing, and comprehensive documentation
- **v0.0.4** - Added Automation API client (Engines, AppBundles, Activities, WorkItems)
- **v0.0.3** - Added Data Management API client (Hubs, Projects, Folders, Items, Versions, Buckets, Objects)
- **v0.0.2** - Added OAuth 2.0 authentication client with 2-legged/3-legged flows, PKCE support, and token management
- **v0.0.1** - Initial package release (placeholder)

</details>

## Contributing

We welcome bug reports and feature requests through [GitHub Issues](https://github.com/voidbox-ai/pyaps/issues).

This project is primarily developed by voidbox. External pull requests have limited review capacity.

## License

Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/voidbox-ai/pyaps)
- [PyPI Package](https://pypi.org/project/py-aps/)
- [Autodesk Platform Services Documentation](https://aps.autodesk.com/)
