"""
工作流引擎

提供工作流定义、执行、状态管理等功能。
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class StepStatus(Enum):
    """步骤状态"""
    PENDING = auto()
    RUNNING = auto()
    SKIPPED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    func: Callable[[Dict[str, Any]], Any]
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    on_success: Optional[Callable[[Any], None]] = None
    on_failure: Optional[Callable[[Exception], None]] = None
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "depends_on": self.depends_on,
            "status": self.status.name,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set_step_result(self, step_id: str, result: Any) -> None:
        self.step_results[step_id] = result

    def get_step_result(self, step_id: str) -> Any:
        return self.step_results.get(step_id)


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Optional[WorkflowContext] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    error: Optional[str] = None

    def add_step(self, step: WorkflowStep) -> None:
        self.steps[step.id] = step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        return self.steps.get(step_id)

    def get_ready_steps(self) -> List[WorkflowStep]:
        ready = []
        completed = {
            step_id for step_id, step in self.steps.items()
            if step.status == StepStatus.COMPLETED
        }

        for step_id, step in self.steps.items():
            if step.status != StepStatus.PENDING:
                continue

            if all(dep in completed for dep in step.depends_on):
                ready.append(step)

        return ready

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.name,
            "steps": {sid: step.to_dict() for sid, step in self.steps.items()},
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_step": self.current_step,
            "error": self.error,
        }


class WorkflowEngine:
    """工作流引擎"""

    _instance: Optional[WorkflowEngine] = None
    _lock = threading.Lock()

    def __new__(cls) -> WorkflowEngine:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._workflows: Dict[str, Workflow] = {}
        self._workflows_lock = threading.Lock()
        self._running_workflows: Set[str] = set()
        self._max_concurrent = 10
        self._on_workflow_complete: Optional[Callable[[Workflow], None]] = None
        self._on_workflow_error: Optional[Callable[[Workflow, Exception], None]] = None
        self._initialized = True

    def create_workflow(
        self,
        name: str,
        steps: Optional[List[WorkflowStep]] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        workflow_id = str(uuid.uuid4())[:8]

        workflow = Workflow(
            id=workflow_id,
            name=name,
            context=WorkflowContext(
                workflow_id=workflow_id,
                variables=variables or {},
            ),
        )

        if steps:
            for step in steps:
                workflow.add_step(step)

        with self._workflows_lock:
            self._workflows[workflow_id] = workflow

        return workflow

    def add_step(
        self,
        workflow_id: str,
        step_id: str,
        name: str,
        func: Callable[[Dict[str, Any]], Any],
        depends_on: Optional[List[str]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        **kwargs,
    ) -> WorkflowStep:
        with self._workflows_lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"工作流 {workflow_id} 不存在")

        step = WorkflowStep(
            id=step_id,
            name=name,
            func=func,
            depends_on=depends_on or [],
            condition=condition,
            **kwargs,
        )

        workflow.add_step(step)
        return step

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        with self._workflows_lock:
            return self._workflows.get(workflow_id)

    def execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
    ) -> bool:
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        workflow.current_step = step.id

        if step.condition:
            try:
                if not step.condition(workflow.context.variables):
                    step.status = StepStatus.SKIPPED
                    step.end_time = datetime.now()
                    return True
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = f"条件检查失败: {str(e)}"
                step.end_time = datetime.now()
                return False

        retries = 0
        last_error = None

        while retries <= step.max_retries:
            try:
                result = step.func(workflow.context.variables)
                step.result = result
                step.status = StepStatus.COMPLETED
                step.end_time = datetime.now()

                workflow.context.set_step_result(step.id, result)

                if step.on_success:
                    try:
                        step.on_success(result)
                    except Exception:
                        pass

                return True

            except Exception as e:
                last_error = str(e)
                retries += 1
                step.retry_count = retries

                if retries <= step.max_retries:
                    time.sleep(1.0 * retries)

        step.status = StepStatus.FAILED
        step.error = last_error
        step.end_time = datetime.now()

        if step.on_failure:
            try:
                step.on_failure(Exception(last_error))
            except Exception:
                pass

        return False

    def run_workflow(self, workflow_id: str) -> bool:
        with self._workflows_lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"工作流 {workflow_id} 不存在")

            if workflow.id in self._running_workflows:
                raise RuntimeError(f"工作流 {workflow_id} 正在运行")

            self._running_workflows.add(workflow.id)

        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now()

        try:
            while True:
                ready_steps = workflow.get_ready_steps()

                if not ready_steps:
                    all_done = all(
                        step.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED)
                        for step in workflow.steps.values()
                    )

                    if all_done:
                        break

                    pending = [
                        s for s in workflow.steps.values()
                        if s.status == StepStatus.PENDING
                    ]

                    if pending:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = "存在无法执行的步骤（依赖未满足）"
                        break

                    time.sleep(0.1)
                    continue

                for step in ready_steps:
                    success = self.execute_step(workflow, step)

                    if not success:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = f"步骤 {step.id} 执行失败: {step.error}"
                        break

                if workflow.status == WorkflowStatus.FAILED:
                    break

            workflow.end_time = datetime.now()

            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.COMPLETED

            if self._on_workflow_complete:
                self._on_workflow_complete(workflow)

            return workflow.status == WorkflowStatus.COMPLETED

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.end_time = datetime.now()

            if self._on_workflow_error:
                self._on_workflow_error(workflow, e)

            return False

        finally:
            with self._workflows_lock:
                self._running_workflows.discard(workflow.id)

    def run_workflow_async(self, workflow_id: str) -> threading.Thread:
        def run():
            self.run_workflow(workflow_id)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def cancel_workflow(self, workflow_id: str) -> bool:
        with self._workflows_lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                return False

            if workflow.status not in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING):
                return False

            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.now()
            return True

    def pause_workflow(self, workflow_id: str) -> bool:
        with self._workflows_lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                return False

            if workflow.status != WorkflowStatus.RUNNING:
                return False

            workflow.status = WorkflowStatus.PAUSED
            return True

    def resume_workflow(self, workflow_id: str) -> bool:
        with self._workflows_lock:
            workflow = self._workflows.get(workflow_id)
            if not workflow:
                return False

            if workflow.status != WorkflowStatus.PAUSED:
                return False

            workflow.status = WorkflowStatus.RUNNING
            return True

    def set_callbacks(
        self,
        on_complete: Optional[Callable[[Workflow], None]] = None,
        on_error: Optional[Callable[[Workflow, Exception], None]] = None,
    ) -> None:
        self._on_workflow_complete = on_complete
        self._on_workflow_error = on_error

    def get_all_workflows(self) -> List[Workflow]:
        with self._workflows_lock:
            return list(self._workflows.values())

    def clear_completed(self) -> int:
        with self._workflows_lock:
            to_remove = [
                wid for wid, w in self._workflows.items()
                if w.status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED)
            ]
            for wid in to_remove:
                del self._workflows[wid]
        return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        with self._workflows_lock:
            workflows = list(self._workflows.values())

        return {
            "total_workflows": len(workflows),
            "running": sum(1 for w in workflows if w.status == WorkflowStatus.RUNNING),
            "completed": sum(1 for w in workflows if w.status == WorkflowStatus.COMPLETED),
            "failed": sum(1 for w in workflows if w.status == WorkflowStatus.FAILED),
            "pending": sum(1 for w in workflows if w.status == WorkflowStatus.PENDING),
        }


def get_workflow_engine() -> WorkflowEngine:
    return WorkflowEngine()
