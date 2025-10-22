# src/pyaps/automation/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

@dataclass
class WorkItemArgument:
    """
    Automation WorkItem 인자(입력/출력 공통 포맷)
    """
    url: str
    verb: Literal["get", "put", "head"] = "get"
    headers: Optional[Dict[str, str]] = None
    local_name: Optional[str] = None
    on_demand: Optional[bool] = None
    unzip: Optional[bool] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "url": self.url,
            "verb": self.verb,
        }
        if self.headers is not None:
            d["headers"] = self.headers
        if self.local_name is not None:
            d["localName"] = self.local_name
        if self.on_demand is not None:
            d["onDemand"] = self.on_demand
        # unzip=True -> 서버에서 압축 해제 (zip=False로 표기)
        if self.unzip is not None:
            d["zip"] = not self.unzip
        if self.description is not None:
            d["description"] = self.description
        return d
    
@dataclass
class WorkItemSpec:
    """
    WorkItem 생성 요청
    - activity_id 예시: '{nickname}.{activity}+{alias}' 또는 '{owner}.{activity}+{alias}'
    - arguments: Activity에서 선언한 파라미터 이름을 key로 사용
    """
    activity_id: str
    arguments: Dict[str, WorkItemArgument] = field(default_factory=dict)
    nickname: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activityId": self.activity_id,
            "arguments": {k: v.to_dict() for k, v in self.arguments.items()},
            **({"nickname": self.nickname} if self.nickname else {}),
        }

@dataclass
class AppBundleSpec:
    """
    AppBundle 생성/버전 생성 시 사용되는 사양의 간단 래퍼
    - 실제 API는 업로드 사전서명(Form) 방식 등을 반환할 수 있으므로,
      여기서는 최소 필드만 캡슐화하고, 나머지는 dict로 직접 전달하도록 설계해야 함
    """
    id: str
    engine: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "engine": self.engine,
        }
        if self.description:
            d["description"] = self.description
        return d

@dataclass
class ActivitySpec:
    """
    Activity 생성/버전 생성용 사양(유연성을 위해 dict 병행 권장)
    """
    id: str
    engine: str
    command_line: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    appbundles: Optional[List[str]] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "engine": self.engine,
            "commandLine": self.command_line,
            "parameters": self.parameters,
        }
        if self.appbundles is not None:
            d["appbundles"] = self.appbundles
        if self.description:
            d["description"] = self.description
        return d