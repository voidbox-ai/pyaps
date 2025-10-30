"""
Design Automation Workflow 사용 예제
파일 업로드 → WorkItem 실행 → 결과 다운로드까지의 전체 워크플로우
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from pyaps.auth import AuthClient, InMemoryTokenStore
from pyaps.automation import (
    AutomationClient,
    AutomationWorkflow,
    DEFAULT_AUTOMATION_SCOPES,
)
from pyaps.datamanagement import DataManagementClient


# Load .env file if exists
def load_dotenv():
    """Simple .env loader"""
    env_file = Path(__file__).parent.parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


load_dotenv()


# Environment variables
APS_CLIENT_ID = os.getenv("APS_CLIENT_ID")
APS_CLIENT_SECRET = os.getenv("APS_CLIENT_SECRET")
APS_REGION = os.getenv("APS_REGION") or "us-east"


def create_workflow() -> AutomationWorkflow:
    """Create AutomationWorkflow instance"""
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
        user_agent="pyaps-automation-workflow",
        timeout=30.0,
    )

    dm = DataManagementClient(
        token_provider=token_provider,
        user_agent="pyaps-automation-workflow",
        timeout=30.0,
    )

    return AutomationWorkflow(
        automation_client=auto,
        data_client=dm,
        default_bucket="my-design-automation-bucket",  # 기본 버킷 설정
        poll_interval=10.0,  # 10초마다 상태 확인
        timeout=3600.0,  # 최대 1시간 대기
    )


def example_simple_workflow():
    """
    가장 간단한 워크플로우 예제:
    로컬 파일 → OSS 업로드 → WorkItem 실행 → 결과 다운로드
    """
    print("\n" + "=" * 60)
    print("Example 1: Simple Workflow")
    print("=" * 60)

    workflow = create_workflow()

    # 전체 워크플로우를 한 번에 실행
    result = workflow.run_workitem_with_files(
        activity_id="myowner.RevitActivity+prod",
        input_files={
            "inputRvt": "path/to/input.rvt",  # 로컬 파일
        },
        output_files={
            "outputRvt": "output.rvt",  # OSS 오브젝트 키
        },
        bucket_key="my-bucket",
        download_outputs=True,  # 완료 후 자동 다운로드
        output_dir="./results",  # 결과 저장 위치
    )

    print(f"WorkItem ID: {result.workitem_id}")
    print(f"Status: {result.status}")
    print(f"Report URL: {result.report_url}")


def example_step_by_step_workflow():
    """
    단계별 워크플로우 예제:
    각 단계를 개별적으로 실행
    """
    print("\n" + "=" * 60)
    print("Example 2: Step-by-Step Workflow")
    print("=" * 60)

    workflow = create_workflow()

    # Step 1: 버킷 확인/생성
    print("\n[Step 1] Ensure bucket exists")
    bucket = workflow.ensure_bucket(
        bucket_key="my-design-automation-bucket",
        region="US",
        policy_key="transient",  # 24시간 보관
    )
    print(f"✓ Bucket ready: {bucket.get('bucketKey')}")

    # Step 2: 입력 파일 업로드
    print("\n[Step 2] Upload input file")
    input_url = workflow.upload_input_file(
        local_path="path/to/input.rvt",
        bucket_key="my-design-automation-bucket",
        object_key="inputs/input.rvt",
    )
    print(f"✓ Input uploaded: {input_url[:50]}...")

    # Step 3: 출력 URL 준비
    print("\n[Step 3] Prepare output URL")
    output_url = workflow.prepare_output_url(
        object_key="outputs/output.rvt",
        bucket_key="my-design-automation-bucket",
    )
    print(f"✓ Output URL ready: {output_url[:50]}...")

    # Step 4: WorkItem 시작
    print("\n[Step 4] Start WorkItem")
    workitem_id = workflow.start_workitem(
        activity_id="myowner.RevitActivity+prod",
        arguments={
            "inputRvt": {"url": input_url, "verb": "get"},
            "outputRvt": {"url": output_url, "verb": "put"},
        },
    )
    print(f"✓ WorkItem started: {workitem_id}")

    # Step 5: 완료 대기
    print("\n[Step 5] Wait for completion")

    def on_progress(status_data):
        status = status_data.get("status")
        progress = status_data.get("progress", "")
        print(f"  Status: {status} {progress}")

    result = workflow.wait_for_completion(
        workitem_id,
        poll_interval=10.0,
        timeout=3600.0,
        on_progress=on_progress,
    )
    print(f"✓ Completed: {result.status}")

    # Step 6: 결과 다운로드
    if result.status == "success":
        print("\n[Step 6] Download output")
        workflow.download_output_file(
            bucket_key="my-design-automation-bucket",
            object_key="outputs/output.rvt",
            local_path="./results/output.rvt",
        )
        print("✓ Output downloaded")


def example_multiple_files():
    """
    여러 파일을 입출력으로 사용하는 예제
    """
    print("\n" + "=" * 60)
    print("Example 3: Multiple Input/Output Files")
    print("=" * 60)

    workflow = create_workflow()

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

    print(f"Status: {result.status}")


def example_batch_processing():
    """
    여러 WorkItem을 배치로 실행하는 예제
    """
    print("\n" + "=" * 60)
    print("Example 4: Batch Processing")
    print("=" * 60)

    workflow = create_workflow()

    # 여러 파일을 처리할 WorkItem 스펙 준비
    workitems = []

    for i in range(1, 6):
        # 각 파일별로 입력/출력 URL 준비
        input_url = workflow.upload_input_file(
            local_path=f"inputs/model_{i}.rvt",
            bucket_key="my-bucket",
            object_key=f"batch/input_{i}.rvt",
        )

        output_url = workflow.prepare_output_url(
            object_key=f"batch/output_{i}.rvt",
            bucket_key="my-bucket",
        )

        workitems.append(
            {
                "activityId": "myowner.RevitActivity+prod",
                "arguments": {
                    "inputRvt": {"url": input_url, "verb": "get"},
                    "outputRvt": {"url": output_url, "verb": "put"},
                },
            }
        )

    # 배치 실행
    results = workflow.run_batch_workitems(
        workitems,
        poll_interval=10.0,
        timeout=3600.0,
    )

    # 결과 확인
    for i, result in enumerate(results, 1):
        print(f"WorkItem {i}: {result.status}")

        if result.status == "success":
            workflow.download_output_file(
                bucket_key="my-bucket",
                object_key=f"batch/output_{i}.rvt",
                local_path=f"./results/output_{i}.rvt",
            )


def example_error_handling():
    """
    에러 처리 예제
    """
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)

    workflow = create_workflow()

    try:
        result = workflow.run_workitem_with_files(
            activity_id="myowner.RevitActivity+prod",
            input_files={"inputRvt": "path/to/input.rvt"},
            output_files={"outputRvt": "output.rvt"},
            bucket_key="my-bucket",
            timeout=600.0,  # 10분 타임아웃
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
        # WorkItem 취소 가능
        # workflow.cancel_workitem(workitem_id)

    except Exception as e:
        print(f"✗ Error: {e}")


def example_webhook_callbacks():
    """
    웹훅 콜백 사용 예제 (onComplete, onProgress)
    """
    print("\n" + "=" * 60)
    print("Example 6: Webhook Callbacks")
    print("=" * 60)

    workflow = create_workflow()

    # 콜백 URL 사용 시 폴링 없이 비동기로 실행 가능
    result = workflow.run_workitem_with_files(
        activity_id="myowner.RevitActivity+prod",
        input_files={"inputRvt": "path/to/input.rvt"},
        output_files={"outputRvt": "output.rvt"},
        bucket_key="my-bucket",
        # WorkItem 완료 시 호출될 웹훅 URL
        on_complete_url="https://myapp.com/api/webhooks/workitem-complete",
        # WorkItem 진행 중 호출될 웹훅 URL (선택)
        on_progress_url="https://myapp.com/api/webhooks/workitem-progress",
    )

    print(f"✓ WorkItem started: {result.workitem_id}")
    print(f"  Complete callback will be sent to: https://myapp.com/api/webhooks/workitem-complete")


def example_webhook_callback_server():
    """
    웹훅 콜백을 받는 서버 예제 (Flask)
    """
    print("\n" + "=" * 60)
    print("Example 7: Webhook Callback Server (Flask)")
    print("=" * 60)

    print("""
# Flask 서버 예제 - 콜백을 받는 엔드포인트

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/webhooks/workitem-complete', methods=['POST'])
def workitem_complete():
    '''
    Design Automation에서 WorkItem 완료 시 호출됨

    Callback payload 구조:
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
    '''
    data = request.json

    workitem_id = data.get('id')
    status = data.get('status')
    report_url = data.get('reportUrl')

    print(f"WorkItem {workitem_id} completed with status: {status}")

    if status == 'success':
        # 성공 처리 로직
        print(f"  Success! Report: {report_url}")
        # 예: 데이터베이스 업데이트, 알림 전송 등

    elif status == 'failed':
        # 실패 처리 로직
        print(f"  Failed! Report: {report_url}")
        # 예: 에러 로깅, 재시도 큐에 추가 등

    return jsonify({"received": True}), 200


@app.route('/api/webhooks/workitem-progress', methods=['POST'])
def workitem_progress():
    '''
    Design Automation에서 WorkItem 진행 중 호출됨

    Callback payload 구조:
    {
        "id": "workitem-id",
        "status": "pending" | "inprogress",
        "progress": "Downloading input files..." | "Processing..." | "Uploading results...",
        ...
    }
    '''
    data = request.json

    workitem_id = data.get('id')
    status = data.get('status')
    progress = data.get('progress', '')

    print(f"WorkItem {workitem_id}: {status} - {progress}")

    # 진행 상황 업데이트 로직 (예: WebSocket으로 실시간 알림)

    return jsonify({"received": True}), 200


if __name__ == '__main__':
    # 프로덕션에서는 HTTPS 필수!
    # ngrok, AWS API Gateway, Azure Functions 등 사용 권장
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
    """)

    print("\n💡 로컬 개발 시 공개 URL 생성 방법:")
    print("  1. ngrok 사용:")
    print("     $ ngrok http 5000")
    print("     → https://abc123.ngrok.io → 이 URL을 on_complete_url에 사용")
    print()
    print("  2. 클라우드 서비스 사용:")
    print("     - AWS API Gateway + Lambda")
    print("     - Azure Functions")
    print("     - Google Cloud Functions")
    print("     - Vercel/Netlify Functions")


def example_webhook_with_signature():
    """
    보안 강화: 서명 검증을 포함한 웹훅 처리 예제
    """
    print("\n" + "=" * 60)
    print("Example 8: Secure Webhook with Signature Verification")
    print("=" * 60)

    print("""
# 서명 검증을 포함한 보안 강화 예제

import hmac
import hashlib
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# 웹훅 비밀키 (환경 변수로 관리 권장)
WEBHOOK_SECRET = "your-secret-key"


def verify_signature(payload: bytes, signature: str) -> bool:
    '''서명 검증'''
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@app.route('/api/webhooks/workitem-complete', methods=['POST'])
def secure_workitem_complete():
    # 1. 서명 검증 (선택사항 - Design Automation은 기본적으로 서명 제공 안 함)
    # signature = request.headers.get('X-Webhook-Signature')
    # if not verify_signature(request.data, signature):
    #     abort(401, "Invalid signature")

    # 2. IP 화이트리스트 검증 (선택사항)
    # allowed_ips = ['52.x.x.x', '54.x.x.x']  # Autodesk IP 범위
    # if request.remote_addr not in allowed_ips:
    #     abort(403, "Forbidden")

    # 3. 요청 데이터 처리
    data = request.json
    workitem_id = data.get('id')

    # 4. 멱등성 보장 (중복 요청 방지)
    # if is_already_processed(workitem_id):
    #     return jsonify({"received": True, "note": "already processed"}), 200

    # 5. 비즈니스 로직 실행
    process_workitem_result(data)

    return jsonify({"received": True}), 200


def process_workitem_result(data):
    '''WorkItem 결과 처리'''
    workitem_id = data.get('id')
    status = data.get('status')

    # 비동기 처리 권장 (Celery, RQ 등)
    # task_queue.enqueue(process_result, workitem_id, status)

    print(f"Processing WorkItem {workitem_id}: {status}")
    """)


def example_progress_monitoring():
    """
    진행 상황 모니터링 예제
    """
    print("\n" + "=" * 60)
    print("Example 6: Progress Monitoring")
    print("=" * 60)

    workflow = create_workflow()

    # 입력/출력 URL 준비
    input_url = workflow.upload_input_file(
        local_path="path/to/input.rvt",
        bucket_key="my-bucket",
    )

    output_url = workflow.prepare_output_url(
        object_key="output.rvt",
        bucket_key="my-bucket",
    )

    # WorkItem 시작
    workitem_id = workflow.start_workitem(
        activity_id="myowner.RevitActivity+prod",
        arguments={
            "inputRvt": {"url": input_url, "verb": "get"},
            "outputRvt": {"url": output_url, "verb": "put"},
        },
    )

    # 상세한 진행 상황 모니터링
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
            time_instr = stats.get("timeInstructionsStarted")
            time_upload = stats.get("timeUploadEnded")

            if time_queued:
                print(f"  Queued at: {time_queued}")
            if time_download:
                print(f"  Download started: {time_download}")
            if time_instr:
                print(f"  Processing started: {time_instr}")
            if time_upload:
                print(f"  Upload ended: {time_upload}")

    result = workflow.wait_for_completion(
        workitem_id,
        on_progress=on_progress,
    )

    print(f"\n✓ Final status: {result.status}")
    if result.report_url:
        print(f"  Report: {result.report_url}")


def main():
    """예제 실행"""
    print("\n" + "=" * 60)
    print("Design Automation Workflow Examples")
    print("=" * 60)

    if not APS_CLIENT_ID or not APS_CLIENT_SECRET:
        print("\n⚠ Set environment variables:")
        print("  export APS_CLIENT_ID='your_client_id'")
        print("  export APS_CLIENT_SECRET='your_client_secret'")
        print("  export APS_REGION='us-east'  # or 'eu-west'")
        return

    print("\n📚 Available examples:")
    print("  1. Simple Workflow - 한 줄로 전체 프로세스 실행")
    print("  2. Step-by-Step - 각 단계를 개별적으로 실행")
    print("  3. Multiple Files - 여러 입출력 파일 처리")
    print("  4. Batch Processing - 여러 WorkItem 배치 실행")
    print("  5. Error Handling - 에러 처리")
    print("  6. Webhook Callbacks - onComplete/onProgress 웹훅 사용")
    print("  7. Webhook Server - Flask 웹훅 서버 예제")
    print("  8. Secure Webhook - 보안 강화 웹훅 처리")
    print("  9. Progress Monitoring - 진행 상황 모니터링")

    print("\n💡 Usage:")
    print("  from pyaps.automation import AutomationWorkflow")
    print("  workflow = AutomationWorkflow(auto_client, dm_client)")
    print("  result = workflow.run_workitem_with_files(...)")


if __name__ == "__main__":
    main()
