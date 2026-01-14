"""Agent Activity Tracker for detailed visibility into agent execution."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of agent activities."""
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETED = "iteration_completed"
    TOOL_USE_STARTED = "tool_use_started"
    TOOL_USE_COMPLETED = "tool_use_completed"
    TOOL_USE_FAILED = "tool_use_failed"
    AGENT_SPAWNED = "agent_spawned"
    THINKING = "thinking"
    MESSAGE = "message"
    QUESTION = "question"
    ANSWER = "answer"
    TASK_UPDATE = "task_update"
    STATUS_CHANGE = "status_change"
    FILE_GENERATED = "file_generated"
    OUTPUT_CREATED = "output_created"
    GIT_COMMIT = "git_commit"


@dataclass
class Activity:
    """Represents a single agent activity."""
    activity_type: ActivityType
    agent_id: str
    agent_name: str
    timestamp: str
    data: Dict[str, Any]
    request_id: str
    parent_agent_id: Optional[str] = None
    iteration: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['activity_type'] = self.activity_type.value
        return result


class AgentActivityTracker:
    """Tracks detailed agent activities for UI visibility."""

    def __init__(self):
        """Initialize activity tracker."""
        self.activities: List[Activity] = []
        self.agent_hierarchy: Dict[str, Dict[str, Any]] = {}
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.pending_questions: Dict[str, Dict[str, Any]] = {}
        self.callbacks: List[Callable[[Activity], None]] = []
        self.max_activities = 10000  # Keep last 10k activities

    def register_callback(self, callback: Callable[[Activity], None]):
        """Register a callback to be called when activities occur."""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[Activity], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _emit_activity(self, activity: Activity):
        """Emit activity to all registered callbacks."""
        # Add to activities list
        self.activities.append(activity)

        # Trim if too long
        if len(self.activities) > self.max_activities:
            self.activities = self.activities[-self.max_activities:]

        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(activity)
            except Exception as e:
                logger.error(f"Error in activity callback: {e}")

    def record_agent_started(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        request_id: str,
        parent_agent_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ):
        """Record agent start."""
        activity = Activity(
            activity_type=ActivityType.AGENT_STARTED,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            parent_agent_id=parent_agent_id,
            data={
                "agent_type": agent_type,
                "input_data": input_data,
                "model": model
            }
        )

        # Update agent hierarchy
        self.agent_hierarchy[agent_id] = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "parent_agent_id": parent_agent_id,
            "children": [],
            "status": "running",
            "started_at": activity.timestamp
        }

        # Link to parent
        if parent_agent_id and parent_agent_id in self.agent_hierarchy:
            if agent_id not in self.agent_hierarchy[parent_agent_id]["children"]:
                self.agent_hierarchy[parent_agent_id]["children"].append(agent_id)

        # Initialize agent state
        self.agent_states[agent_id] = {
            "status": "running",
            "current_task": "Initializing...",
            "current_iteration": 0,
            "max_iterations": None,
            "started_at": activity.timestamp,
            "activities": []
        }

        self._emit_activity(activity)

    def record_iteration_started(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        iteration: int,
        max_iterations: int,
        prompt: Optional[str] = None
    ):
        """Record iteration start."""
        activity = Activity(
            activity_type=ActivityType.ITERATION_STARTED,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            iteration=iteration,
            data={
                "iteration": iteration,
                "max_iterations": max_iterations,
                "prompt": prompt[:200] if prompt else None  # Truncate for brevity
            }
        )

        # Update agent state
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["current_iteration"] = iteration
            self.agent_states[agent_id]["max_iterations"] = max_iterations
            self.agent_states[agent_id]["current_task"] = f"Thinking... (iteration {iteration}/{max_iterations})"

        self._emit_activity(activity)

    def record_tool_use(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        iteration: int,
        tool_name: str,
        tool_inputs: Dict[str, Any],
        status: str = "started"  # started, completed, failed
    ):
        """Record tool use."""
        activity_type = {
            "started": ActivityType.TOOL_USE_STARTED,
            "completed": ActivityType.TOOL_USE_COMPLETED,
            "failed": ActivityType.TOOL_USE_FAILED
        }.get(status, ActivityType.TOOL_USE_STARTED)

        activity = Activity(
            activity_type=activity_type,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            iteration=iteration,
            data={
                "tool_name": tool_name,
                "tool_inputs": tool_inputs,
                "status": status
            }
        )

        # Update agent state
        if agent_id in self.agent_states:
            if status == "started":
                self.agent_states[agent_id]["current_task"] = f"Using tool: {tool_name}"
            elif status == "completed":
                self.agent_states[agent_id]["current_task"] = f"Processing {tool_name} result..."

        self._emit_activity(activity)

    def record_agent_spawned(
        self,
        parent_agent_id: str,
        parent_agent_name: str,
        spawned_agent_id: str,
        spawned_agent_name: str,
        request_id: str
    ):
        """Record agent spawn."""
        activity = Activity(
            activity_type=ActivityType.AGENT_SPAWNED,
            agent_id=parent_agent_id,
            agent_name=parent_agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "spawned_agent_id": spawned_agent_id,
                "spawned_agent_name": spawned_agent_name
            }
        )

        self._emit_activity(activity)

    def record_message(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        message: str,
        message_type: str = "info"  # info, warning, error, success
    ):
        """Record an agent message."""
        activity = Activity(
            activity_type=ActivityType.MESSAGE,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "message": message,
                "message_type": message_type
            }
        )

        self._emit_activity(activity)

    def record_question(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        question_id: str,
        question: str,
        options: Optional[List[str]] = None
    ):
        """Record agent question that needs user response."""
        activity = Activity(
            activity_type=ActivityType.QUESTION,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "question_id": question_id,
                "question": question,
                "options": options
            }
        )

        # Add to pending questions
        self.pending_questions[question_id] = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "question": question,
            "options": options,
            "asked_at": activity.timestamp,
            "answered": False
        }

        # Update agent state
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["status"] = "awaiting_user_input"
            self.agent_states[agent_id]["current_task"] = "Waiting for user response..."

        self._emit_activity(activity)

    def record_answer(
        self,
        question_id: str,
        answer: str
    ):
        """Record user answer to agent question."""
        if question_id not in self.pending_questions:
            logger.warning(f"Answer provided for unknown question: {question_id}")
            return

        question_info = self.pending_questions[question_id]

        activity = Activity(
            activity_type=ActivityType.ANSWER,
            agent_id=question_info["agent_id"],
            agent_name=question_info["agent_name"],
            timestamp=datetime.now().isoformat(),
            request_id="",  # Would need to track this
            data={
                "question_id": question_id,
                "question": question_info["question"],
                "answer": answer
            }
        )

        # Mark question as answered
        self.pending_questions[question_id]["answered"] = True
        self.pending_questions[question_id]["answer"] = answer

        # Update agent state
        agent_id = question_info["agent_id"]
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["status"] = "running"
            self.agent_states[agent_id]["current_task"] = "Processing user response..."

        self._emit_activity(activity)

    def record_task_update(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        task_description: str
    ):
        """Record task update."""
        activity = Activity(
            activity_type=ActivityType.TASK_UPDATE,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "task_description": task_description
            }
        )

        # Update agent state
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["current_task"] = task_description

        self._emit_activity(activity)

    def record_agent_completed(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """Record agent completion."""
        activity = Activity(
            activity_type=ActivityType.AGENT_COMPLETED,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "result": result
            }
        )

        # Update agent hierarchy
        if agent_id in self.agent_hierarchy:
            self.agent_hierarchy[agent_id]["status"] = "completed"
            self.agent_hierarchy[agent_id]["completed_at"] = activity.timestamp

        # Update agent state
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["status"] = "completed"
            self.agent_states[agent_id]["current_task"] = "Completed"
            self.agent_states[agent_id]["completed_at"] = activity.timestamp

            # Extract completion details for UI visibility
            if result:
                self.agent_states[agent_id]["summary"] = result.get("summary", "")
                self.agent_states[agent_id]["self_analysis"] = result.get("self_analysis", "")
                self.agent_states[agent_id]["deliverables"] = result.get("deliverables", [])
            else:
                self.agent_states[agent_id]["summary"] = ""
                self.agent_states[agent_id]["self_analysis"] = ""
                self.agent_states[agent_id]["deliverables"] = []

        self._emit_activity(activity)

    def record_agent_failed(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        error: str,
        traceback: Optional[str] = None
    ):
        """Record agent failure."""
        activity = Activity(
            activity_type=ActivityType.AGENT_FAILED,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "error": error,
                "traceback": traceback
            }
        )

        # Update agent hierarchy
        if agent_id in self.agent_hierarchy:
            self.agent_hierarchy[agent_id]["status"] = "failed"
            self.agent_hierarchy[agent_id]["failed_at"] = activity.timestamp
            self.agent_hierarchy[agent_id]["error"] = error

        # Update agent state
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["status"] = "failed"
            self.agent_states[agent_id]["current_task"] = f"Failed: {error}"
            self.agent_states[agent_id]["failed_at"] = activity.timestamp

        self._emit_activity(activity)

    def record_file_generated(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        file_path: str,
        file_size: int,
        file_type: str,
        preview: Optional[str] = None
    ):
        """Record file generation."""
        activity = Activity(
            activity_type=ActivityType.FILE_GENERATED,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "preview": preview
            }
        )

        self._emit_activity(activity)

    def record_git_commit(
        self,
        agent_id: str,
        agent_name: str,
        request_id: str,
        commit_hash: str,
        commit_message: str,
        files: List[str]
    ):
        """Record git commit."""
        activity = Activity(
            activity_type=ActivityType.GIT_COMMIT,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            request_id=request_id,
            data={
                "commit_hash": commit_hash,
                "commit_message": commit_message,
                "files": files
            }
        )

        self._emit_activity(activity)

    def get_activities(
        self,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
        activity_types: Optional[List[ActivityType]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get activities with optional filtering."""
        filtered = self.activities

        if agent_id:
            filtered = [a for a in filtered if a.agent_id == agent_id]

        if request_id:
            filtered = [a for a in filtered if a.request_id == request_id]

        if activity_types:
            filtered = [a for a in filtered if a.activity_type in activity_types]

        # Return most recent first
        filtered = list(reversed(filtered[-limit:]))

        return [a.to_dict() for a in filtered]

    def get_agent_hierarchy(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get agent hierarchy tree."""
        if not request_id:
            return self.agent_hierarchy

        # Filter by request_id
        # This would require storing request_id in hierarchy
        return self.agent_hierarchy

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an agent."""
        return self.agent_states.get(agent_id)

    def get_all_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent states."""
        return self.agent_states

    def get_pending_questions(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending questions."""
        return {
            qid: qdata for qid, qdata in self.pending_questions.items()
            if not qdata.get("answered", False)
        }

    def clear_request(self, request_id: str):
        """Clear all data for a request."""
        # Remove activities
        self.activities = [a for a in self.activities if a.request_id != request_id]

        # Remove from hierarchy and states
        # (This is tricky without tracking request_id in hierarchy)
        # For now, we'll keep the data
