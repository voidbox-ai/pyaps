"""
APS Design Automation API 사용 예제
AppBundles, Activities, WorkItems 등의 기능을 smoke test 형태로 시연
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from pyaps.auth import AuthClient, Scopes, InMemoryTokenStore
from pyaps.automation.client import AutomationClient, DEFAULT_AUTOMATION_SCOPES
from pyaps.datamanagement import DataManagementClient
from pyaps.http.client import HTTPError


# Load .env file if exists
def load_dotenv():
    """Simple .env loader"""
    env_file = Path(__file__).parent.parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_dotenv()


# Environment variables
APS_CLIENT_ID = os.getenv("APS_CLIENT_ID")
APS_CLIENT_SECRET = os.getenv("APS_CLIENT_SECRET")
APS_REGION = os.getenv("APS_REGION") or "us-east"


def _print_hdr(title: str):
    print(f"\n{title}")
    print("-" * len(title))


def _p(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def create_clients():
    """Create auth and automation clients"""
    auth_client = AuthClient(
        client_id=APS_CLIENT_ID,
        client_secret=APS_CLIENT_SECRET,
        store=InMemoryTokenStore(),
    )

    def token_provider() -> str:
        token = auth_client.two_legged.get_token(DEFAULT_AUTOMATION_SCOPES)
        return token.access_token

    auto = AutomationClient(
        token_provider=token_provider,
        region=APS_REGION,
        user_agent="pyaps-automation-smoke",
        timeout=30.0,
    )

    dm = DataManagementClient(
        token_provider=token_provider,
        user_agent="pyaps-automation-smoke",
        timeout=30.0,
    )

    return auto, dm


def example_engines():
    """Engines API 예제"""
    print("\n" + "="*60)
    print("1. Engines API")
    print("="*60)

    auto, _ = create_clients()

    # 1-1. List engines
    print("\n[1-1] List available engines")
    try:
        engines = auto.list_engines(page=1, page_size=50)
        data = engines.get('data', [])
        print(f"  ✓ Found {len(data)} engines")
        for engine in data[:5]:
            print(f"    - {engine}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_forgeapps():
    """ForgeApps API 예제"""
    print("\n" + "="*60)
    print("2. ForgeApps API")
    print("="*60)

    auto, _ = create_clients()

    # 2-1. Get me
    print("\n[2-1] Get current app information")
    try:
        me = auto.get_me()
        _p(me)
    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_appbundles():
    """AppBundles API 예제"""
    print("\n" + "="*60)
    print("3. AppBundles API")
    print("="*60)

    auto, _ = create_clients()

    # 3-1. List appbundles
    print("\n[3-1] List appbundles")
    try:
        bundles = auto.list_appbundles()
        data = bundles.get('data', [])
        print(f"  ✓ Found {len(data)} appbundles")
        for bundle in data[:3]:
            print(f"    - {bundle}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # 3-2. Create appbundle (structure only)
    print("\n[3-2] Create appbundle (structure only)")
    print("  Usage:")
    print("    appbundle = auto.create_appbundle({")
    print("        'id': 'MyAppBundle',")
    print("        'engine': 'Autodesk.Revit+2023',")
    print("        'description': 'My custom Revit addin'")
    print("    })")

    # 3-3. Upload appbundle zip (structure only)
    print("\n[3-3] Upload appbundle zip (structure only)")
    print("  Workflow:")
    print("    1. Create appbundle: response = auto.create_appbundle({...})")
    print("    2. Upload zip: auto.upload_appbundle_zip_from_create(response, 'bundle.zip')")
    print("    3. Create alias: auto.create_appbundle_alias('MyAppBundle', {'id': 'prod', 'version': 1})")

    # 3-4. Manage versions (structure only)
    print("\n[3-4] Manage appbundle versions (structure only)")
    print("  Create new version:")
    print("    version = auto.create_appbundle_version('MyAppBundle', {")
    print("        'engine': 'Autodesk.Revit+2023',")
    print("        'description': 'Version 2'")
    print("    })")
    print("    auto.upload_appbundle_zip_from_version(version, 'bundle_v2.zip')")
    print("    auto.set_appbundle_alias('MyAppBundle', 'prod', version=2)")


def example_activities():
    """Activities API 예제"""
    print("\n" + "="*60)
    print("4. Activities API")
    print("="*60)

    auto, _ = create_clients()

    # 4-1. List activities
    print("\n[4-1] List activities")
    try:
        activities = auto.list_activities()
        data = activities.get('data', [])
        print(f"  ✓ Found {len(data)} activities")
        for activity in data[:3]:
            print(f"    - {activity}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # 4-2. Create activity (structure only)
    print("\n[4-2] Create activity (structure only)")
    print("  Usage:")
    print("    activity = auto.create_activity({")
    print("        'id': 'MyActivity',")
    print("        'engine': 'Autodesk.Revit+2023',")
    print("        'commandLine': [")
    print("            '$(engine.path)\\\\revitcoreconsole.exe /i \"$(args[inputFile].path)\" /al \"$(appbundles[MyBundle].path)\"'")
    print("        ],")
    print("        'parameters': {")
    print("            'inputFile': {'verb': 'get', 'description': 'Input RVT file'},")
    print("            'outputFile': {'verb': 'put', 'description': 'Output RVT file'}")
    print("        },")
    print("        'appbundles': ['Owner.MyAppBundle+prod']")
    print("    })")

    # 4-3. Manage activity versions (structure only)
    print("\n[4-3] Manage activity versions (structure only)")
    print("  Create alias:")
    print("    auto.create_activity_alias('MyActivity', {'id': 'prod', 'version': 1})")
    print("  Create new version:")
    print("    auto.create_activity_version('MyActivity', {...})")
    print("  Update alias:")
    print("    auto.set_activity_alias('MyActivity', 'prod', version=2)")


def example_workitems():
    """WorkItems API 예제"""
    print("\n" + "="*60)
    print("5. WorkItems API")
    print("="*60)

    print("\n[5-1] Start workitem (structure only)")
    print("  Workflow:")
    print("    # 1. Prepare input/output signed URLs (using OSS)")
    print("    input_url = '...'  # signed download URL")
    print("    output_url = '...' # signed upload URL")
    print()
    print("    # 2. Start workitem")
    print("    workitem = auto.start_workitem({")
    print("        'activityId': 'Owner.MyActivity+prod',")
    print("        'arguments': {")
    print("            'inputFile': {'url': input_url, 'verb': 'get'},")
    print("            'outputFile': {'url': output_url, 'verb': 'put'}")
    print("        }")
    print("    })")
    print("    workitem_id = workitem['id']")
    print()
    print("    # 3. Poll workitem status")
    print("    while True:")
    print("        status = auto.get_workitem(workitem_id)")
    print("        if status['status'] in ('success', 'failed', 'cancelled'):")
    print("            break")
    print("        time.sleep(10)")

    print("\n[5-2] Batch workitems (structure only)")
    print("  Usage:")
    print("    workitems = [")
    print("        {'activityId': '...', 'arguments': {...}},")
    print("        {'activityId': '...', 'arguments': {...}}")
    print("    ]")
    print("    batch = auto.create_workitems_batch(workitems)")
    print("    batch_ids = [wi['id'] for wi in batch]")
    print("    status = auto.get_workitems_status(batch_ids)")

    print("\n[5-3] Cancel workitem (structure only)")
    print("  Usage:")
    print("    auto.cancel_workitem(workitem_id)")


def example_service_limits():
    """Service Limits API 예제"""
    print("\n" + "="*60)
    print("6. Service Limits API")
    print("="*60)

    print("\n[6-1] Get service limits (structure only)")
    print("  Usage:")
    print("    limits = auto.get_service_limits('owner_id')")
    print("    print(limits)")
    print()
    print("  Example response:")
    print("    {")
    print("      'maxConcurrentWorkitems': 10,")
    print("      'maxWorkitemDuration': 3600")
    print("    }")


def example_complete_workflow():
    """Complete workflow example"""
    print("\n" + "="*60)
    print("7. Complete Workflow Example")
    print("="*60)

    print("\nComplete Design Automation workflow:")
    print()
    print("Step 1: Create and upload AppBundle")
    print("  appbundle = auto.create_appbundle({")
    print("      'id': 'MyBundle',")
    print("      'engine': 'Autodesk.Revit+2023',")
    print("      'description': 'My Revit addin'")
    print("  })")
    print("  auto.upload_appbundle_zip_from_create(appbundle, 'bundle.zip')")
    print("  auto.create_appbundle_alias('MyBundle', {'id': 'prod', 'version': 1})")
    print()
    print("Step 2: Create Activity")
    print("  activity = auto.create_activity({")
    print("      'id': 'MyActivity',")
    print("      'engine': 'Autodesk.Revit+2023',")
    print("      'commandLine': ['...'],")
    print("      'parameters': {...},")
    print("      'appbundles': ['Owner.MyBundle+prod']")
    print("  })")
    print("  auto.create_activity_alias('MyActivity', {'id': 'prod', 'version': 1})")
    print()
    print("Step 3: Prepare input/output files (using Data Management)")
    print("  # Upload input file to OSS")
    print("  signed_input = dm.objects.get_signed_download(bucket, 'input.rvt')")
    print("  input_url = signed_input['url']")
    print()
    print("  # Prepare output upload URL")
    print("  signed_output = dm.objects.get_signed_upload(bucket, 'output.rvt')")
    print("  output_url = signed_output['urls'][0]")
    print()
    print("Step 4: Execute WorkItem")
    print("  workitem = auto.start_workitem({")
    print("      'activityId': 'Owner.MyActivity+prod',")
    print("      'arguments': {")
    print("          'inputFile': {'url': input_url, 'verb': 'get'},")
    print("          'outputFile': {'url': output_url, 'verb': 'put'}")
    print("      }")
    print("  })")
    print()
    print("Step 5: Monitor and download results")
    print("  # Poll until completion")
    print("  status = auto.get_workitem(workitem['id'])")
    print("  # Download output file from OSS when status == 'success'")


def main():
    """모든 예제 실행"""
    print("\n" + "="*60)
    print("APS Design Automation API - Smoke Test Examples")
    print("="*60)
    print("\nℹ Set environment variables before running:")
    print("  export APS_CLIENT_ID='your_client_id'")
    print("  export APS_CLIENT_SECRET='your_client_secret'")
    print("  export APS_REGION='us-east'  # or 'eu-west'")

    # 환경 변수 체크
    has_credentials = bool(APS_CLIENT_ID and APS_CLIENT_SECRET)

    if has_credentials:
        print("\n✓ Credentials found - running live examples")

        # Live examples
        example_forgeapps()
        example_engines()
        example_appbundles()
        example_activities()
    else:
        print("\n⚠ Credentials not found - showing structure only")

    # Structure-only examples (always show)
    example_workitems()
    example_service_limits()
    example_complete_workflow()

    print("\n" + "="*60)
    print("✓ All examples completed")
    print("="*60)
    print("\n📚 For complete AppBundle workflow, you'll need:")
    print("  - AppBundle zip file (Revit/Inventor/AutoCAD plugin)")
    print("  - Input files stored in OSS")
    print("  - Activity definition matching your AppBundle")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as e:
        print(f"\nHTTPError: [{e.status}] {e.method} {e.url}")
        if e.body:
            print(f"Response: {e.body[:500]}")
        raise
    except Exception as e:
        print(f"\nError: {e}")
        raise
