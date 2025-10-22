"""
APS Data Management API 사용 예제
Hubs, Projects, Folders, Items, Versions, Buckets, Objects 등의 기능을 smoke test 형태로 시연
"""
from __future__ import annotations

import os
from pathlib import Path
from pyaps.auth import AuthClient, Scopes, InMemoryTokenStore
from pyaps.datamanagement.client import DataManagementClient


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


def create_dm_client() -> DataManagementClient:
    """Create DataManagementClient with 3-legged token provider"""
    auth_client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
        store=InMemoryTokenStore(),
    )

    # For Data Management, we typically use 2-legged with data:read/write scopes
    def token_provider() -> str:
        scopes = [Scopes.DATA_READ, Scopes.DATA_WRITE, Scopes.BUCKET_READ]
        token = auth_client.two_legged.get_token(scopes)
        return token.access_token

    return DataManagementClient(token_provider=token_provider)


def example_hubs():
    """Hubs API 예제"""
    print("\n" + "="*60)
    print("1. Hubs API")
    print("="*60)

    dm = create_dm_client()

    # 1-1. List hubs
    print("\n[1-1] List accessible hubs")
    try:
        hubs = list(dm.hubs.list(limit=10))
        print(f"  ✓ Found {len(hubs)} hubs")

        if not hubs:
            print("  ℹ No hubs found. You may need 3-legged authentication for BIM 360/ACC.")
            return None, None

        for hub in hubs[:3]:
            hub_data = hub.get('attributes', {})
            print(f"    - {hub_data.get('name', 'N/A')} (ID: {hub.get('id', 'N/A')})")

        # 1-2. Get hub details
        print("\n[1-2] Get hub details")
        first_hub_id = hubs[0]['id']
        hub_detail = dm.hubs.get(first_hub_id)
        hub_attrs = hub_detail.get('data', {}).get('attributes', {})
        print(f"  ✓ Hub: {hub_attrs.get('name')}")
        print(f"  ✓ Region: {hub_attrs.get('region')}")

        # 1-3. List projects in hub
        print("\n[1-3] List projects in hub")
        projects = list(dm.hubs.list_projects(first_hub_id, limit=5))
        print(f"  ✓ Found {len(projects)} projects")
        for proj in projects[:3]:
            proj_attrs = proj.get('attributes', {})
            print(f"    - {proj_attrs.get('name', 'N/A')} (ID: {proj.get('id', 'N/A')})")

        return first_hub_id, projects[0]['id'] if projects else None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None


def example_projects(hub_id: str, project_id: str):
    """Projects API 예제"""
    print("\n" + "="*60)
    print("2. Projects API")
    print("="*60)

    if not hub_id or not project_id:
        print("  ℹ Skipped - no hub/project available")
        return None

    dm = create_dm_client()

    # 2-1. Get project details
    print("\n[2-1] Get project details")
    try:
        project = dm.projects.get(hub_id, project_id)
        proj_data = project.get('data', {})
        proj_attrs = proj_data.get('attributes', {})
        print(f"  ✓ Project: {proj_attrs.get('name')}")
        print(f"  ✓ Type: {proj_data.get('type')}")

        # 2-2. Get top folders
        print("\n[2-2] Get top folders")
        top_folders_resp = dm.projects.top_folders(hub_id, project_id)
        top_folders = top_folders_resp.get('data', [])
        print(f"  ✓ Found {len(top_folders)} top folders")
        for folder in top_folders[:3]:
            folder_attrs = folder.get('attributes', {})
            print(f"    - {folder_attrs.get('name', 'N/A')} (ID: {folder.get('id', 'N/A')})")

        return top_folders[0]['id'] if top_folders else None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def example_folders(project_id: str, folder_id: str):
    """Folders API 예제"""
    print("\n" + "="*60)
    print("3. Folders API")
    print("="*60)

    if not project_id or not folder_id:
        print("  ℹ Skipped - no project/folder available")
        return

    dm = create_dm_client()

    # 3-1. Get folder details
    print("\n[3-1] Get folder details")
    try:
        folder = dm.folders.get(project_id, folder_id)
        folder_data = folder.get('data', {})
        folder_attrs = folder_data.get('attributes', {})
        print(f"  ✓ Folder: {folder_attrs.get('name')}")
        print(f"  ✓ Hidden: {folder_attrs.get('hidden', False)}")

        # 3-2. List folder contents
        print("\n[3-2] List folder contents")
        contents = list(dm.folders.contents(project_id, folder_id, limit=10))
        print(f"  ✓ Found {len(contents)} items")
        for item in contents[:5]:
            item_attrs = item.get('attributes', {})
            item_type = item.get('type', 'unknown')
            print(f"    - [{item_type}] {item_attrs.get('displayName') or item_attrs.get('name', 'N/A')}")

        # 3-3. Search in folder (structure only)
        print("\n[3-3] Search in folder (structure only)")
        print("  Usage:")
        print(f"    results = dm.folders.search('{project_id}', '{folder_id}', q='*.rvt')")
        print("    for item in results:")
        print("        print(item['attributes']['displayName'])")

        # 3-4. Create subfolder (structure only)
        print("\n[3-4] Create subfolder (structure only)")
        print("  Usage:")
        print(f"    new_folder = dm.folders.create(")
        print(f"        project_id='{project_id}',")
        print(f"        parent_folder_id='{folder_id}',")
        print(f"        name='New Subfolder'")
        print(f"    )")

    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_items():
    """Items & Versions API 예제"""
    print("\n" + "="*60)
    print("4. Items & Versions API")
    print("="*60)

    print("\n[4-1] Get item details (structure only)")
    print("  Usage:")
    print("    item = dm.items.get(project_id, item_id)")
    print("    print(item['data']['attributes']['displayName'])")

    print("\n[4-2] List item versions (structure only)")
    print("  Usage:")
    print("    versions = dm.items.list_versions(project_id, item_id)")
    print("    for version in versions:")
    print("        print(version['attributes']['versionNumber'])")

    print("\n[4-3] Create item with first version (structure only)")
    print("  Workflow:")
    print("    1. Create storage: storage = dm.objects.create_storage(project_id, folder_id, 'file.rvt')")
    print("    2. Upload file: dm.objects.upload_via_storage(storage, file_bytes)")
    print("    3. Create item: item = dm.items.create_with_first_version(")
    print("        project_id, folder_id, 'file.rvt', storage['data']['id'])")

    print("\n[4-4] Create new version (structure only)")
    print("  Usage:")
    print("    new_version = dm.versions.create(project_id, item_id, 'file_v2.rvt', storage_urn)")


def example_buckets():
    """Buckets API 예제"""
    print("\n" + "="*60)
    print("5. Buckets API (OSS v2)")
    print("="*60)

    dm = create_dm_client()

    # 5-1. List buckets
    print("\n[5-1] List buckets")
    try:
        buckets = list(dm.buckets.list(limit=10))
        print(f"  ✓ Found {len(buckets)} buckets")
        for bucket in buckets[:3]:
            bucket_key = bucket.get('bucketKey', 'N/A')
            print(f"    - {bucket_key}")

        # 5-2. Create bucket (structure only)
        print("\n[5-2] Create bucket (structure only)")
        print("  Usage:")
        print("    new_bucket = dm.buckets.create(")
        print("        bucket_key='my-unique-bucket-key',")
        print("        region='US',")
        print("        policy_key='transient'  # or 'temporary', 'persistent'")
        print("    )")

        if buckets:
            # 5-3. Get bucket details
            print("\n[5-3] Get bucket details")
            first_bucket_key = buckets[0].get('bucketKey')
            bucket = dm.buckets.get(first_bucket_key)
            print(f"  ✓ Bucket: {bucket.get('bucketKey')}")
            print(f"  ✓ Policy: {bucket.get('policyKey')}")

            # 5-4. List objects in bucket
            print("\n[5-4] List objects in bucket")
            objects = list(dm.buckets.list_objects(first_bucket_key, limit=5))
            print(f"  ✓ Found {len(objects)} objects")
            for obj in objects[:3]:
                print(f"    - {obj.get('objectKey', 'N/A')} ({obj.get('size', 0)} bytes)")

    except Exception as e:
        print(f"  ✗ Error: {e}")


def example_objects():
    """Objects API 예제"""
    print("\n" + "="*60)
    print("6. Objects API (Storage & Upload)")
    print("="*60)

    print("\n[6-1] Create storage for upload (structure only)")
    print("  Usage:")
    print("    storage = dm.objects.create_storage(")
    print("        project_id='b.project_id',")
    print("        target_folder_id='urn:adsk.wipprod:fs.folder:xxxxx',")
    print("        file_name='sample.rvt'")
    print("    )")

    print("\n[6-2] Upload file via storage (structure only)")
    print("  Usage:")
    print("    with open('local_file.rvt', 'rb') as f:")
    print("        dm.objects.upload_via_storage(storage, f.read())")

    print("\n[6-3] Get signed upload URL (OSS) (structure only)")
    print("  Usage:")
    print("    signed = dm.objects.get_signed_upload(")
    print("        bucket_key='my-bucket',")
    print("        object_key='path/to/file.txt',")
    print("        parts=1  # single-part upload")
    print("    )")

    print("\n[6-4] Complete signed upload (structure only)")
    print("  Usage:")
    print("    result = dm.objects.complete_signed_upload(")
    print("        bucket_key='my-bucket',")
    print("        object_key='path/to/file.txt',")
    print("        upload_key=signed['uploadKey']")
    print("    )")

    print("\n[6-5] Get signed download URL (structure only)")
    print("  Usage:")
    print("    download = dm.objects.get_signed_download(")
    print("        bucket_key='my-bucket',")
    print("        object_key='path/to/file.txt',")
    print("        minutes_valid=60")
    print("    )")
    print("    # Then use download['url'] to download the file")


def example_commands():
    """Commands API 예제"""
    print("\n" + "="*60)
    print("7. Commands API (Advanced)")
    print("="*60)

    print("\n[7-1] Move/Copy items (structure only)")
    print("  Usage:")
    print("    command = dm.commands.post(project_id, {")
    print("        'data': {")
    print("            'type': 'commands',")
    print("            'attributes': {")
    print("                'extension': {")
    print("                    'type': 'commands:autodesk.core:MoveTo',")
    print("                    'version': '1.0.0'")
    print("                }")
    print("            },")
    print("            'relationships': {")
    print("                'resources': {'data': [{'type': 'items', 'id': 'item_id'}]},")
    print("                'target': {'data': {'type': 'folders', 'id': 'target_folder_id'}}")
    print("            }")
    print("        }")
    print("    })")


def example_workflow():
    """Complete workflow: Upload file to project"""
    print("\n" + "="*60)
    print("8. Complete Upload Workflow Example")
    print("="*60)

    print("\nWorkflow to upload a file to APS project:")
    print("\n  Step 1: Get project and folder IDs")
    print("    hubs = list(dm.hubs.list())")
    print("    projects = list(dm.hubs.list_projects(hub_id))")
    print("    top_folders = dm.projects.top_folders(hub_id, project_id)")
    print("    folder_id = top_folders['data'][0]['id']")

    print("\n  Step 2: Create storage location")
    print("    storage = dm.objects.create_storage(")
    print("        project_id=project_id,")
    print("        target_folder_id=folder_id,")
    print("        file_name='myfile.rvt'")
    print("    )")

    print("\n  Step 3: Upload file to storage")
    print("    with open('myfile.rvt', 'rb') as f:")
    print("        dm.objects.upload_via_storage(storage, f.read())")

    print("\n  Step 4: Create item with first version")
    print("    item = dm.items.create_with_first_version(")
    print("        project_id=project_id,")
    print("        parent_folder_id=folder_id,")
    print("        file_name='myfile.rvt',")
    print("        storage_urn=storage['data']['id']")
    print("    )")
    print("    print(f'✓ File uploaded: {item[\"id\"]}')")


def main():
    """모든 예제 실행"""
    print("\n" + "="*60)
    print("APS Data Management API - Smoke Test Examples")
    print("="*60)
    print("\nℹ Set environment variables before running:")
    print("  export APS_CLIENT_ID='your_client_id'")
    print("  export APS_CLIENT_SECRET='your_client_secret'")

    # 환경 변수 체크
    has_credentials = bool(os.getenv("APS_CLIENT_ID") and os.getenv("APS_CLIENT_SECRET"))

    if has_credentials:
        print("\n✓ Credentials found - running live examples")

        # Live examples
        hub_id, project_id = example_hubs()
        if hub_id and project_id:
            folder_id = example_projects(hub_id, project_id)
            if folder_id:
                example_folders(project_id, folder_id)

        example_buckets()
    else:
        print("\n⚠ Credentials not found - showing structure only")

    # Structure-only examples (always show)
    example_items()
    example_objects()
    example_commands()
    example_workflow()

    print("\n" + "="*60)
    print("✓ All examples completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
