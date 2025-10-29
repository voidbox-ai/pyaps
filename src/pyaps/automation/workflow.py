# src/pyaps/automation/workflow.py
"""
Design Automation 워크플로우 추상화
OSS 버킷/오브젝트 준비 → WorkItem 실행 → 결과 다운로드까지의 전체 과정을 통합
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple
from dataclasses import dataclass

from pyaps.automation.client import AutomationClient
from pyaps.automation.types import WorkItemSpec, WorkItemArgument
from pyaps.datamanagement.client import DataManagementClient

WorkItemStatus = Literal["pending", "inprogress", "success", "failed", "cancelled"]


@dataclass
class WorkItemResult:
    """WorkItem 실행 결과"""
    workitem_id: str
    status: WorkItemStatus
    report_url: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


class AutomationWorkflow:
    """
    Design Automation WorkItem 실행을 위한 고수준 워크플로우

    주요 기능:
    1. OSS 버킷/오브젝트 생성 및 파일 업로드
    2. WorkItem 실행 및 상태 모니터링
    3. 결과물 다운로드
    """

    def __init__(
        self,
        automation_client: AutomationClient,
        data_client: DataManagementClient,
        *,
        default_bucket: Optional[str] = None,
        poll_interval: float = 10.0,
        timeout: float = 3600.0,
    ):
        """
        Args:
            automation_client: Design Automation API 클라이언트
            data_client: Data Management API 클라이언트 (OSS 접근용)
            default_bucket: 기본 OSS 버킷 키
            poll_interval: WorkItem 상태 폴링 간격 (초)
            timeout: WorkItem 최대 대기 시간 (초)
        """
        self.auto = automation_client
        self.dm = data_client
        self.default_bucket = default_bucket
        self.poll_interval = poll_interval
        self.timeout = timeout

    # ==================== Step 1: OSS 준비 ====================

    def ensure_bucket(
        self,
        bucket_key: str,
        *,
        region: str = "US",
        policy_key: str = "transient",
    ) -> Dict[str, Any]:
        """
        OSS 버킷 생성 (이미 존재하면 무시)

        Args:
            bucket_key: 버킷 키 (소문자, 숫자, 하이픈만 허용, 3-128자)
            region: 리전 (US, EMEA 등)
            policy_key: 보관 정책 (transient=24시간, temporary=30일, persistent=영구)

        Returns:
            버킷 정보
        """
        try:
            return self.dm.buckets.get(bucket_key)
        except Exception:
            # 버킷이 없으면 생성
            return self.dm.buckets.create(
                bucket_key,
                region=region,
                policy_key=policy_key,
            )

    def upload_input_file(
        self,
        local_path: str | Path,
        *,
        bucket_key: Optional[str] = None,
        object_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """
        입력 파일을 OSS에 업로드하고 다운로드 URL 반환

        Args:
            local_path: 로컬 파일 경로
            bucket_key: OSS 버킷 키 (미지정시 default_bucket 사용)
            object_key: OSS 오브젝트 키 (미지정시 파일명 사용)
            timeout: 업로드 타임아웃

        Returns:
            Signed download URL (WorkItem arguments에서 사용)
        """
        bucket_key = bucket_key or self.default_bucket
        if not bucket_key:
            raise ValueError("bucket_key must be provided or default_bucket must be set")

        local_path = Path(local_path)
        object_key = object_key or local_path.name

        # OSS에 업로드
        signed_upload = self.dm.objects.post_signed(
            bucket_key, object_key, access="readwrite"
        )

        with open(local_path, "rb") as f:
            file_data = f.read()

        self.dm.objects.upload_via_signed(signed_upload, file_data, timeout=timeout)

        # 다운로드 URL 생성 (WorkItem에서 사용할 것)
        signed_download = self.dm.objects.get_signed_download(
            bucket_key, object_key, minutes_valid=60
        )
        return signed_download.get("url") or signed_download.get("signedUrl")

    def prepare_output_url(
        self,
        object_key: str,
        *,
        bucket_key: Optional[str] = None,
        minutes_valid: int = 60,
    ) -> str:
        """
        출력 파일용 업로드 URL 생성

        Args:
            object_key: OSS 오브젝트 키
            bucket_key: OSS 버킷 키 (미지정시 default_bucket 사용)
            minutes_valid: URL 유효 시간 (분)

        Returns:
            Signed upload URL (WorkItem arguments에서 사용)
        """
        bucket_key = bucket_key or self.default_bucket
        if not bucket_key:
            raise ValueError("bucket_key must be provided or default_bucket must be set")

        # 업로드용 signed URL 생성
        signed = self.dm.objects.post_signed(
            bucket_key, object_key, access="readwrite"
        )
        return signed.get("url") or signed.get("signedUrl")

    # ==================== Step 2: WorkItem 실행 ====================

    def start_workitem(
        self,
        activity_id: str,
        arguments: Dict[str, WorkItemArgument | Dict[str, Any]],
        *,
        nickname: Optional[str] = None,
        on_complete: Optional[str] = None,
        on_progress: Optional[str] = None,
    ) -> str:
        """
        WorkItem 시작

        Args:
            activity_id: Activity 전체 ID (예: 'owner.ActivityName+alias')
            arguments: Activity 파라미터별 입출력 URL
            nickname: WorkItem 별칭 (선택)
            on_complete: WorkItem 완료 시 호출될 콜백 URL (HTTP POST로 WorkItem 정보 전송)
            on_progress: WorkItem 진행 상황 업데이트 시 호출될 콜백 URL (HTTP POST)

        Returns:
            WorkItem ID

        Note:
            콜백 URL은 공개적으로 접근 가능한 HTTPS 엔드포인트여야 합니다.
            onComplete 콜백에는 WorkItem 상태, 결과, 통계 등이 포함된 JSON이 전송됩니다.
        """
        # WorkItemArgument 변환
        converted_args = {}
        for key, arg in arguments.items():
            if isinstance(arg, dict):
                converted_args[key] = WorkItemArgument(**arg)
            else:
                converted_args[key] = arg

        spec = WorkItemSpec(
            activity_id=activity_id,
            arguments=converted_args,
            nickname=nickname,
            on_complete=on_complete,
            on_progress=on_progress,
        )

        result = self.auto.start_workitem(spec)
        return result["id"]

    def wait_for_completion(
        self,
        workitem_id: str,
        *,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> WorkItemResult:
        """
        WorkItem 완료 대기

        Args:
            workitem_id: WorkItem ID
            poll_interval: 폴링 간격 (초)
            timeout: 최대 대기 시간 (초)
            on_progress: 진행 상황 콜백 함수

        Returns:
            WorkItem 실행 결과

        Raises:
            TimeoutError: 타임아웃 발생
            RuntimeError: WorkItem 실행 실패
        """
        poll_interval = poll_interval or self.poll_interval
        timeout = timeout or self.timeout

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"WorkItem {workitem_id} timed out after {timeout}s"
                )

            status_data = self.auto.get_workitem(workitem_id)
            status = status_data.get("status")

            if on_progress:
                on_progress(status_data)

            if status in ("success", "failed", "cancelled"):
                return WorkItemResult(
                    workitem_id=workitem_id,
                    status=status,
                    report_url=status_data.get("reportUrl"),
                    stats=status_data.get("stats"),
                    details=status_data,
                )

            time.sleep(poll_interval)

    def cancel_workitem(self, workitem_id: str) -> None:
        """WorkItem 취소"""
        self.auto.cancel_workitem(workitem_id)

    # ==================== Step 3: 결과 다운로드 ====================

    def download_output_file(
        self,
        bucket_key: str,
        object_key: str,
        local_path: str | Path,
    ) -> None:
        """
        OSS에서 출력 파일 다운로드

        Args:
            bucket_key: OSS 버킷 키
            object_key: OSS 오브젝트 키
            local_path: 저장할 로컬 경로
        """
        # Signed download URL 생성
        signed = self.dm.objects.get_signed_download(
            bucket_key, object_key, minutes_valid=10
        )
        url = signed.get("url") or signed.get("signedUrl")

        # 파일 다운로드
        import requests
        response = requests.get(url, timeout=300)
        response.raise_for_status()

        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as f:
            f.write(response.content)

    # ==================== 통합 워크플로우 ====================

    def run_workitem_with_files(
        self,
        activity_id: str,
        input_files: Optional[Dict[str, str | Path]] = None,
        output_files: Optional[Dict[str, str]] = None,
        *,
        bucket_key: Optional[str] = None,
        download_outputs: bool = True,
        output_dir: Optional[str | Path] = None,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete_url: Optional[str] = None,
        on_progress_url: Optional[str] = None,
    ) -> WorkItemResult:
        """
        파일 업로드 → WorkItem 실행 → 결과 다운로드 전체 워크플로우

        Args:
            activity_id: Activity 전체 ID
            input_files: 입력 파일 매핑 {argument_name: local_file_path} (선택, None 또는 {} 가능)
            output_files: 출력 파일 매핑 {argument_name: object_key} (선택, None 또는 {} 가능)
            bucket_key: OSS 버킷 키 (입력/출력 파일이 있을 때만 필요)
            download_outputs: 완료 후 출력 파일 자동 다운로드 여부
            output_dir: 출력 파일 저장 디렉토리
            poll_interval: 폴링 간격 (초)
            timeout: 최대 대기 시간 (초)
            on_progress: 진행 상황 콜백 함수 (로컬 폴링용)
            on_complete_url: WorkItem 완료 시 호출될 웹훅 URL (Design Automation에서 HTTP POST)
            on_progress_url: WorkItem 진행 중 호출될 웹훅 URL (Design Automation에서 HTTP POST)

        Returns:
            WorkItem 실행 결과

        Example:
            >>> # 일반적인 사용
            >>> result = workflow.run_workitem_with_files(
            ...     activity_id="myowner.RevitActivity+prod",
            ...     input_files={"inputRvt": "input.rvt"},
            ...     output_files={"outputRvt": "output.rvt"},
            ...     bucket_key="my-bucket",
            ... )
            >>>
            >>> # 입력 없이 출력만 생성 (예: 템플릿 생성)
            >>> result = workflow.run_workitem_with_files(
            ...     activity_id="myowner.TemplateGenerator+prod",
            ...     output_files={"outputRvt": "template.rvt"},
            ...     bucket_key="my-bucket",
            ... )
            >>>
            >>> # 로그만 생성 (입출력 파일 없음)
            >>> result = workflow.run_workitem_with_files(
            ...     activity_id="myowner.ValidationActivity+prod",
            ... )

        Note:
            on_complete_url을 사용하면 폴링 없이 비동기로 결과를 받을 수 있습니다.
            콜백 URL은 공개적으로 접근 가능한 HTTPS 엔드포인트여야 합니다.
        """
        input_files = input_files or {}
        output_files = output_files or {}

        # 파일이 있는 경우에만 버킷 확인
        if input_files or output_files:
            bucket_key = bucket_key or self.default_bucket
            if not bucket_key:
                raise ValueError(
                    "bucket_key must be provided or default_bucket must be set when using input_files or output_files"
                )
            # 버킷 확인/생성
            self.ensure_bucket(bucket_key)

        # 1. 입력 파일 업로드
        arguments: Dict[str, WorkItemArgument] = {}

        for arg_name, local_path in input_files.items():
            url = self.upload_input_file(local_path, bucket_key=bucket_key)
            arguments[arg_name] = WorkItemArgument(url=url, verb="get")

        # 2. 출력 URL 준비
        for arg_name, object_key in output_files.items():
            url = self.prepare_output_url(object_key, bucket_key=bucket_key)
            arguments[arg_name] = WorkItemArgument(url=url, verb="put")

        # 3. WorkItem 실행 (콜백 URL 포함)
        workitem_id = self.start_workitem(
            activity_id,
            arguments,
            on_complete=on_complete_url,
            on_progress=on_progress_url,
        )

        # 4. 완료 대기
        result = self.wait_for_completion(
            workitem_id,
            poll_interval=poll_interval,
            timeout=timeout,
            on_progress=on_progress,
        )

        # 5. 결과 다운로드
        if download_outputs and result.status == "success" and output_files:
            output_dir = Path(output_dir) if output_dir else Path.cwd()

            for arg_name, object_key in output_files.items():
                local_path = output_dir / object_key
                self.download_output_file(bucket_key, object_key, local_path)

        return result

    # ==================== 배치 처리 ====================

    def run_batch_workitems(
        self,
        workitems: List[Dict[str, Any]],
        *,
        poll_interval: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> List[WorkItemResult]:
        """
        여러 WorkItem을 배치로 실행하고 모두 완료될 때까지 대기

        Args:
            workitems: WorkItem 스펙 목록
            poll_interval: 폴링 간격 (초)
            timeout: 최대 대기 시간 (초)

        Returns:
            각 WorkItem의 실행 결과 목록
        """
        # 배치 시작
        batch_result = self.auto.create_workitems_batch(workitems)
        workitem_ids = [wi["id"] for wi in batch_result]

        # 모든 WorkItem 완료 대기
        results = []
        for workitem_id in workitem_ids:
            result = self.wait_for_completion(
                workitem_id,
                poll_interval=poll_interval,
                timeout=timeout,
            )
            results.append(result)

        return results
