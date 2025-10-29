# AutomationWorkflow User Guide

High-level workflow abstraction for executing Design Automation WorkItems.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
  - [OSS Preparation](#1-oss-preparation)
  - [WorkItem Execution](#2-workitem-execution)
  - [Result Download](#3-result-download)
  - [Unified Workflow](#4-unified-workflow)
  - [Batch Processing](#5-batch-processing)
- [Webhook Callbacks](#webhook-callbacks)
- [Advanced Usage](#advanced-usage)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Overview

`AutomationWorkflow` provides a unified interface for Design Automation WorkItem execution:

1. **OSS Bucket/Object Creation** - Prepare storage for input/output files
2. **File Upload** - Upload local files to OSS and generate signed URLs
3. **WorkItem Execution** - Execute Activity and monitor status
4. **Result Download** - Download completed results to local filesystem

---

## Quick Start

### 1. Initialize Clients

```python
from pyaps.auth import AuthClient, InMemoryTokenStore
from pyaps.automation import AutomationClient, AutomationWorkflow, DEFAULT_AUTOMATION_SCOPES
from pyaps.datamanagement import DataManagementClient

# Authentication setup
auth_client = AuthClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    store=InMemoryTokenStore(),
)

def token_provider() -> str:
    token = auth_client.two_legged.get_token(DEFAULT_AUTOMATION_SCOPES)
    return token.access_token

# Design Automation client
auto_client = AutomationClient(
    token_provider=token_provider,
    region="us-east",
)

# Data Management client
dm_client = DataManagementClient(
    token_provider=token_provider,
)

# Initialize workflow
workflow = AutomationWorkflow(
    automation_client=auto_client,
    data_client=dm_client,
    default_bucket="my-design-automation-bucket",
    poll_interval=10.0,  # Check status every 10 seconds
    timeout=3600.0,      # Max wait time: 1 hour
)
```

### 2. Simplest Usage

```python
# Execute entire workflow in one call
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={
        "inputRvt": "path/to/input.rvt",
    },
    output_files={
        "outputRvt": "output.rvt",
    },
    bucket_key="my-bucket",
    download_outputs=True,
    output_dir="./results",
)

print(f"Status: {result.status}")
print(f"WorkItem ID: {result.workitem_id}")
print(f"Report URL: {result.report_url}")
```

---

## Core Features

### 1. OSS Preparation

#### 1.1 Create/Ensure Bucket

```python
bucket = workflow.ensure_bucket(
    bucket_key="my-design-automation-bucket",
    region="US",              # US, EMEA, etc.
    policy_key="transient",   # transient (24h), temporary (30d), persistent (forever)
)
```

#### 1.2 Upload Input File

```python
# Upload local file to OSS and get download URL
input_url = workflow.upload_input_file(
    local_path="path/to/input.rvt",
    bucket_key="my-bucket",
    object_key="inputs/input.rvt",  # Optional, defaults to filename
    timeout=300.0,
)
```

#### 1.3 Prepare Output URL

```python
# Generate upload URL for output file
output_url = workflow.prepare_output_url(
    object_key="outputs/output.rvt",
    bucket_key="my-bucket",
    minutes_valid=60,  # URL validity in minutes
)
```

---

### 2. WorkItem Execution

#### 2.1 Start WorkItem

```python
workitem_id = workflow.start_workitem(
    activity_id="myowner.RevitActivity+prod",
    arguments={
        "inputRvt": {"url": input_url, "verb": "get"},
        "outputRvt": {"url": output_url, "verb": "put"},
    },
    nickname="MyWorkItem",  # Optional
)
```

#### 2.2 Wait for Completion

```python
def on_progress(status_data):
    status = status_data.get("status")
    progress = status_data.get("progress", "")
    print(f"Status: {status} - {progress}")

result = workflow.wait_for_completion(
    workitem_id,
    poll_interval=10.0,
    timeout=3600.0,
    on_progress=on_progress,  # Optional callback
)

if result.status == "success":
    print("WorkItem succeeded!")
elif result.status == "failed":
    print(f"WorkItem failed. Report: {result.report_url}")
```

#### 2.3 Cancel WorkItem

```python
workflow.cancel_workitem(workitem_id)
```

---

### 3. Result Download

```python
workflow.download_output_file(
    bucket_key="my-bucket",
    object_key="outputs/output.rvt",
    local_path="./results/output.rvt",
)
```

---

### 4. Unified Workflow

#### 4.1 Single Input/Output

```python
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={
        "inputRvt": "path/to/input.rvt",
    },
    output_files={
        "outputRvt": "output.rvt",
    },
    bucket_key="my-bucket",
)
```

#### 4.2 Multiple Input/Output Files

```python
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={
        "inputRvt": "path/to/model.rvt",
        "configJson": "path/to/config.json",
        "templateRvt": "path/to/template.rvt",
    },
    output_files={
        "outputRvt": "results/processed.rvt",
        "reportPdf": "results/report.pdf",
        "exportIfc": "results/export.ifc",
    },
    bucket_key="my-bucket",
    download_outputs=True,
    output_dir="./results",
)
```

#### 4.3 Optional Input/Output Files

Some Activities may not require input files or may only generate logs without output files:

```python
# No input files - Generate template from scratch
result = workflow.run_workitem_with_files(
    activity_id="myowner.TemplateGenerator+prod",
    output_files={
        "outputRvt": "template.rvt",
    },
    bucket_key="my-bucket",
)

# No output files - Validation only (logs in report)
result = workflow.run_workitem_with_files(
    activity_id="myowner.ValidationActivity+prod",
    input_files={
        "inputRvt": "model.rvt",
    },
    bucket_key="my-bucket",
)

# No files at all - Health check or scheduled task
result = workflow.run_workitem_with_files(
    activity_id="myowner.HealthCheck+prod",
)
# Note: bucket_key not required when no files are involved

# You can also pass empty dictionaries explicitly
result = workflow.run_workitem_with_files(
    activity_id="myowner.MyActivity+prod",
    input_files={},
    output_files={},
)
```

#### 4.4 Progress Monitoring

```python
import time

def on_progress(status_data):
    status = status_data.get("status")
    progress = status_data.get("progress", "")
    stats = status_data.get("stats", {})

    print(f"\n[{time.strftime('%H:%M:%S')}] Status: {status}")

    if progress:
        print(f"  Progress: {progress}")

    if stats:
        time_queued = stats.get("timeQueued")
        time_download = stats.get("timeDownloadStarted")
        time_processing = stats.get("timeInstructionsStarted")

        if time_queued:
            print(f"  Queued at: {time_queued}")
        if time_download:
            print(f"  Download started: {time_download}")
        if time_processing:
            print(f"  Processing started: {time_processing}")

result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    on_progress=on_progress,
)
```

---

### 5. Batch Processing

Execute multiple WorkItems concurrently:

```python
# Prepare batch WorkItem specifications
workitems = []

for i in range(1, 6):
    input_url = workflow.upload_input_file(
        local_path=f"inputs/model_{i}.rvt",
        bucket_key="my-bucket",
        object_key=f"batch/input_{i}.rvt",
    )

    output_url = workflow.prepare_output_url(
        object_key=f"batch/output_{i}.rvt",
        bucket_key="my-bucket",
    )

    workitems.append({
        "activityId": "myowner.RevitActivity+prod",
        "arguments": {
            "inputRvt": {"url": input_url, "verb": "get"},
            "outputRvt": {"url": output_url, "verb": "put"},
        },
    })

# Execute batch
results = workflow.run_batch_workitems(
    workitems,
    poll_interval=10.0,
    timeout=3600.0,
)

# Process results
for i, result in enumerate(results, 1):
    print(f"WorkItem {i}: {result.status}")

    if result.status == "success":
        workflow.download_output_file(
            bucket_key="my-bucket",
            object_key=f"batch/output_{i}.rvt",
            local_path=f"./results/output_{i}.rvt",
        )
```

---

## Webhook Callbacks

Use webhooks instead of polling to receive WorkItem results asynchronously.

### 1. Basic Usage

```python
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    # Webhook URL called on WorkItem completion
    on_complete_url="https://myapp.com/api/webhooks/workitem-complete",
    # Webhook URL called during WorkItem progress (optional)
    on_progress_url="https://myapp.com/api/webhooks/workitem-progress",
)
```

### 2. Webhook Server Implementation (Flask)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/webhooks/workitem-complete', methods=['POST'])
def workitem_complete():
    """
    Called by Design Automation when WorkItem completes

    Callback payload:
    {
        "id": "workitem-id",
        "status": "success" | "failed" | "cancelled",
        "reportUrl": "https://...",
        "stats": {
            "timeQueued": "2024-01-01T00:00:00Z",
            "timeDownloadStarted": "2024-01-01T00:00:10Z",
            "timeInstructionsStarted": "2024-01-01T00:00:20Z",
            "timeInstructionsEnded": "2024-01-01T00:05:00Z",
            "timeUploadEnded": "2024-01-01T00:05:30Z"
        },
        "activityId": "owner.ActivityName+alias",
        ...
    }
    """
    data = request.json

    workitem_id = data.get('id')
    status = data.get('status')
    report_url = data.get('reportUrl')

    print(f"WorkItem {workitem_id} completed with status: {status}")

    if status == 'success':
        # Success handling logic
        # e.g., Update database, send notifications, download results
        pass
    elif status == 'failed':
        # Failure handling logic
        # e.g., Log errors, add to retry queue
        pass

    return jsonify({"received": True}), 200


@app.route('/api/webhooks/workitem-progress', methods=['POST'])
def workitem_progress():
    """
    Called by Design Automation during WorkItem execution

    Callback payload:
    {
        "id": "workitem-id",
        "status": "pending" | "inprogress",
        "progress": "Downloading input files..." | "Processing..." | "Uploading results...",
        ...
    }
    """
    data = request.json

    workitem_id = data.get('id')
    status = data.get('status')
    progress = data.get('progress', '')

    print(f"WorkItem {workitem_id}: {status} - {progress}")

    # Progress update logic
    # e.g., WebSocket real-time notifications, database updates

    return jsonify({"received": True}), 200


if __name__ == '__main__':
    # HTTPS required in production!
    app.run(host='0.0.0.0', port=5000)
```

### 3. Public URL for Local Development

Webhook URLs must be **publicly accessible HTTPS endpoints** that Design Automation can reach.

#### Using ngrok

```bash
# 1. Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# 2. Run ngrok
ngrok http 5000

# 3. Use generated URL
# Forwarding: https://abc123.ngrok.io -> http://localhost:5000
# → on_complete_url="https://abc123.ngrok.io/api/webhooks/workitem-complete"
```

#### Using Cloud Services

- **AWS API Gateway + Lambda**
- **Azure Functions**
- **Google Cloud Functions**
- **Vercel/Netlify Functions**

### 4. Security Enhancement

```python
import hmac
import hashlib
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

WEBHOOK_SECRET = "your-secret-key"  # Recommended: use environment variable

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@app.route('/api/webhooks/workitem-complete', methods=['POST'])
def secure_workitem_complete():
    # 1. Signature verification (optional - Design Automation doesn't provide signatures by default)
    # signature = request.headers.get('X-Webhook-Signature')
    # if not verify_signature(request.data, signature):
    #     abort(401, "Invalid signature")

    # 2. IP whitelist verification (optional)
    # allowed_ips = ['52.x.x.x', '54.x.x.x']  # Autodesk IP ranges
    # if request.remote_addr not in allowed_ips:
    #     abort(403, "Forbidden")

    # 3. Process request data
    data = request.json
    workitem_id = data.get('id')

    # 4. Ensure idempotency (prevent duplicate processing)
    # if is_already_processed(workitem_id):
    #     return jsonify({"received": True, "note": "already processed"}), 200

    # 5. Execute business logic
    process_workitem_result(data)

    return jsonify({"received": True}), 200
```

---

## Advanced Usage

### 1. Step-by-Step Workflow Control

For fine-grained control over the entire process:

```python
# Step 1: Ensure bucket exists
bucket = workflow.ensure_bucket("my-bucket")

# Step 2: Upload input file
input_url = workflow.upload_input_file(
    local_path="path/to/input.rvt",
    bucket_key="my-bucket",
)

# Step 3: Prepare output URL
output_url = workflow.prepare_output_url(
    object_key="output.rvt",
    bucket_key="my-bucket",
)

# Step 4: Start WorkItem
workitem_id = workflow.start_workitem(
    activity_id="myowner.RevitActivity+prod",
    arguments={
        "inputRvt": {"url": input_url, "verb": "get"},
        "outputRvt": {"url": output_url, "verb": "put"},
    },
)

# Step 5: Wait for completion
result = workflow.wait_for_completion(workitem_id)

# Step 6: Download results
if result.status == "success":
    workflow.download_output_file(
        bucket_key="my-bucket",
        object_key="output.rvt",
        local_path="./results/output.rvt",
    )
```

### 2. Custom Timeout Settings

```python
# Increase timeout for long-running jobs
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "large-model.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    poll_interval=30.0,   # Check every 30 seconds
    timeout=7200.0,       # Wait up to 2 hours
)
```

### 3. Selective Download

```python
# Disable automatic download (keep results in OSS only)
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    download_outputs=False,  # Don't download
)

# Download manually when needed
if result.status == "success":
    workflow.download_output_file(
        bucket_key="my-bucket",
        object_key="output.rvt",
        local_path="./results/output.rvt",
    )
```

---

## Error Handling

### 1. Basic Error Handling

```python
from pyaps.automation import AutomationError
from pyaps.http import HTTPError

try:
    result = workflow.run_workitem_with_files(
        activity_id="myowner.RevitActivity+prod",
        input_files={"inputRvt": "input.rvt"},
        output_files={"outputRvt": "output.rvt"},
        bucket_key="my-bucket",
        timeout=600.0,
    )

    if result.status == "success":
        print("✓ WorkItem succeeded")
    elif result.status == "failed":
        print(f"✗ WorkItem failed")
        print(f"Report URL: {result.report_url}")
        if result.details:
            print(f"Error details: {result.details}")

except TimeoutError as e:
    print(f"✗ Timeout: {e}")
    # Can cancel WorkItem if needed
    # workflow.cancel_workitem(workitem_id)

except AutomationError as e:
    print(f"✗ Automation error: {e}")
    print(f"Status: {e.status}")
    print(f"Payload: {e.payload}")

except HTTPError as e:
    print(f"✗ HTTP error: {e}")
    print(f"Status: {e.status}")
    print(f"Body: {e.body}")

except ValueError as e:
    print(f"✗ Configuration error: {e}")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
```

### 2. Retry Logic

```python
import time

def run_with_retry(workflow, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            result = workflow.run_workitem_with_files(
                activity_id="myowner.RevitActivity+prod",
                input_files={"inputRvt": "input.rvt"},
                output_files={"outputRvt": "output.rvt"},
                bucket_key="my-bucket",
            )

            if result.status == "success":
                return result
            elif result.status == "failed":
                print(f"Attempt {attempt} failed. Report: {result.report_url}")
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        except TimeoutError as e:
            print(f"Attempt {attempt} timed out: {e}")
            if attempt < max_retries:
                time.sleep(60)

        except Exception as e:
            print(f"Attempt {attempt} error: {e}")
            if attempt < max_retries:
                time.sleep(30)

    raise RuntimeError(f"Failed after {max_retries} attempts")

# Usage
result = run_with_retry(workflow)
```

---

## Best Practices

### 1. Use Environment Variables

```python
import os

workflow = AutomationWorkflow(
    automation_client=auto_client,
    data_client=dm_client,
    default_bucket=os.getenv("APS_DEFAULT_BUCKET", "my-default-bucket"),
    poll_interval=float(os.getenv("APS_POLL_INTERVAL", "10.0")),
    timeout=float(os.getenv("APS_TIMEOUT", "3600.0")),
)
```

### 2. Choose Appropriate Bucket Policy

- **transient** (24 hours): Testing and temporary work
- **temporary** (30 days): Short-term projects
- **persistent** (forever): Long-term storage needs

```python
workflow.ensure_bucket(
    bucket_key="test-bucket",
    policy_key="transient",  # For testing
)

workflow.ensure_bucket(
    bucket_key="production-bucket",
    policy_key="persistent",  # For production
)
```

### 3. Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def on_progress(status_data):
    status = status_data.get("status")
    progress = status_data.get("progress", "")
    logger.info(f"WorkItem status: {status} - {progress}")

result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    on_progress=on_progress,
)
```

### 4. Resource Cleanup

```python
from pyaps.datamanagement import DataManagementClient

# Clean up temporary files
def cleanup_temporary_files(dm_client: DataManagementClient, bucket_key: str):
    """Delete temporary files older than 24 hours"""
    import time

    for obj in dm_client.buckets.list_objects(bucket_key):
        object_key = obj.get("objectKey")
        # Check creation time and delete if needed
        # ...
```

### 5. Webhooks vs Polling

| Method | Pros | Cons | Use Cases |
|--------|------|------|-----------|
| **Webhooks** | - Resource efficient<br>- Immediate notifications<br>- Serverless friendly | - Requires public endpoint<br>- More complex implementation | - Production environment<br>- Long-running jobs<br>- Multiple WorkItems |
| **Polling** | - Simple implementation<br>- Easy local development | - Resource wasteful<br>- Polling delay | - Development/testing<br>- Single WorkItem<br>- Immediate results needed |

```python
# Development/Testing: Use polling
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    poll_interval=10.0,
)

# Production: Use webhooks
result = workflow.run_workitem_with_files(
    activity_id="myowner.RevitActivity+prod",
    input_files={"inputRvt": "input.rvt"},
    output_files={"outputRvt": "output.rvt"},
    bucket_key="my-bucket",
    on_complete_url="https://myapp.com/webhooks/complete",
)
```

---

## API Reference

### AutomationWorkflow

#### Constructor

```python
AutomationWorkflow(
    automation_client: AutomationClient,
    data_client: DataManagementClient,
    *,
    default_bucket: Optional[str] = None,
    poll_interval: float = 10.0,
    timeout: float = 3600.0,
)
```

#### Main Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `ensure_bucket(bucket_key, *, region, policy_key)` | Create or get existing bucket | `Dict[str, Any]` |
| `upload_input_file(local_path, *, bucket_key, object_key, timeout)` | Upload input file | `str` (signed URL) |
| `prepare_output_url(object_key, *, bucket_key, minutes_valid)` | Generate output URL | `str` (signed URL) |
| `start_workitem(activity_id, arguments, *, nickname, on_complete, on_progress)` | Start WorkItem | `str` (workitem_id) |
| `wait_for_completion(workitem_id, *, poll_interval, timeout, on_progress)` | Wait for completion | `WorkItemResult` |
| `cancel_workitem(workitem_id)` | Cancel WorkItem | `None` |
| `download_output_file(bucket_key, object_key, local_path)` | Download result | `None` |
| `run_workitem_with_files(activity_id, input_files, output_files, ...)` | Unified workflow | `WorkItemResult` |
| `run_batch_workitems(workitems, *, poll_interval, timeout)` | Batch processing | `List[WorkItemResult]` |

### WorkItemResult

```python
@dataclass
class WorkItemResult:
    workitem_id: str
    status: WorkItemStatus  # "pending" | "inprogress" | "success" | "failed" | "cancelled"
    report_url: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
```

---

## Related Documentation

- [AutomationClient API](./client.py) - Low-level API wrapper
- [WorkItemSpec](./types.py) - WorkItem specification types
- [Example Code](./workflow_example.py) - Runnable example code
- [APS Design Automation API Docs](https://aps.autodesk.com/en/docs/design-automation/v3/)

---

## Troubleshooting

### Q: "bucket_key must be provided" error

```python
# If default_bucket is not set, explicitly pass bucket_key
workflow = AutomationWorkflow(
    automation_client=auto_client,
    data_client=dm_client,
    default_bucket="my-bucket",  # Add this
)
```

### Q: TimeoutError occurs

```python
# Increase timeout or use webhooks
result = workflow.run_workitem_with_files(
    ...,
    timeout=7200.0,  # 2 hours
    # Or use webhooks
    on_complete_url="https://myapp.com/webhooks/complete",
)
```

### Q: Webhook not being called

1. **Check HTTPS**: HTTP is not supported
2. **Public access**: localhost won't work (use ngrok, etc.)
3. **Response code**: Ensure endpoint returns 200 OK
4. **Timeout**: Webhook endpoint should respond quickly

### Q: WorkItem status is "failed"

```python
# Check Report URL
if result.status == "failed":
    print(f"Report URL: {result.report_url}")
    # Open in browser to see detailed error logs
```

---

**Version**: 0.0.4
**Last Updated**: 2025-01-30
