from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    task_type: str
    duration_minutes: int
    priority: Priority
    completed: bool = False
    scheduled_time: Optional[str] = None  # "HH:MM" format
    frequency: Frequency = Frequency.ONCE
    due_date: Optional[date] = None

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == Priority.HIGH

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as completed. Returns a new Task for the next occurrence if recurring."""
        self.completed = True
        if self.frequency == Frequency.DAILY:
            return self._create_next_occurrence(days=1)
        elif self.frequency == Frequency.WEEKLY:
            return self._create_next_occurrence(days=7)
        return None

    def _create_next_occurrence(self, days: int) -> "Task":
        """Create the next recurring instance of this task."""
        next_due = (self.due_date or date.today()) + timedelta(days=days)
        return Task(
            title=self.title,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            scheduled_time=self.scheduled_time,
            frequency=self.frequency,
            due_date=next_due,
        )


@dataclass
class Pet:
    """Stores pet details and the list of care tasks assigned to it."""

    name: str
    species: str
    age: int
    special_needs: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> None:
        """Mark a task complete and auto-add the next occurrence if recurring."""
        next_task = task.mark_complete()
        if next_task:
            self.tasks.append(next_task)

    def summary(self) -> str:
        """Return a readable one-line description of the pet."""
        needs = f", special needs: {', '.join(self.special_needs)}" if self.special_needs else ""
        return f"{self.name} ({self.species}, age {self.age}{needs})"


@dataclass
class Owner:
    """Represents the pet owner with their available time and list of pets."""

    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks if not task.completed]

    def can_fit(self, task: Task, used_minutes: int) -> bool:
        """Return True if the task fits within the owner's remaining available time."""
        return used_minutes + task.duration_minutes <= self.available_minutes


class ScheduledPlan:
    """The output of the scheduler — an ordered plan with reasoning and conflict warnings."""

    def __init__(
        self,
        scheduled_tasks: List[Task],
        skipped_tasks: List[Task],
        total_time: int,
        reasoning: dict,
        conflicts: List[str],
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_time = total_time
        self.reasoning = reasoning
        self.conflicts = conflicts

    def display(self) -> str:
        """Format the plan as a readable string for terminal or UI output."""
        lines = ["=== Today's Schedule ===\n"]

        if self.conflicts:
            lines.append("⚠️  CONFLICTS DETECTED:")
            for c in self.conflicts:
                lines.append(f"  ⚠ {c}")
            lines.append("")

        if self.scheduled_tasks:
            for i, task in enumerate(self.scheduled_tasks, 1):
                reason = self.reasoning.get(task.title, "")
                time_str = f" @ {task.scheduled_time}" if task.scheduled_time else ""
                lines.append(
                    f"  {i}. {task.title}{time_str} ({task.duration_minutes} min) [{task.priority.value}]"
                )
                if reason:
                    lines.append(f"     → {reason}")
        else:
            lines.append("  No tasks scheduled.")

        lines.append(f"\nTotal time: {self.total_time} min")

        if self.skipped_tasks:
            lines.append("\n--- Skipped ---")
            for task in self.skipped_tasks:
                reason = self.reasoning.get(task.title, "")
                lines.append(f"  • {task.title} ({task.duration_minutes} min)")
                if reason:
                    lines.append(f"     → {reason}")

        return "\n".join(lines)


class Scheduler:
    """Retrieves tasks from the owner's pets and builds a prioritized daily plan."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by their scheduled_time (HH:MM). Tasks without a time go to the end."""
        return sorted(tasks, key=lambda t: (t.scheduled_time is None, t.scheduled_time or ""))

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        task_type: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by pet name, completion status, or task type."""
        result = tasks
        if pet_name is not None:
            pet_task_titles = set()
            for pet in self.owner.pets:
                if pet.name == pet_name:
                    pet_task_titles = {t.title for t in pet.tasks}
            result = [t for t in result if t.title in pet_task_titles]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if task_type is not None:
            result = [t for t in result if t.task_type == task_type]
        return result

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Detect tasks scheduled at the same time and return warning messages."""
        warnings: List[str] = []
        timed = [t for t in tasks if t.scheduled_time is not None]
        by_time: dict[str, List[Task]] = {}
        for task in timed:
            by_time.setdefault(task.scheduled_time, []).append(task)
        for time_slot, group in by_time.items():
            if len(group) > 1:
                names = ", ".join(f'"{t.title}"' for t in group)
                warnings.append(f"Time conflict at {time_slot}: {names}")
        return warnings

    def generate_schedule(self) -> ScheduledPlan:
        """Sort tasks by time then priority, detect conflicts, greedily schedule what fits."""
        all_tasks = self.owner.get_all_tasks()

        # Sort: first by scheduled time, then by priority within each group
        sorted_tasks = sorted(
            all_tasks,
            key=lambda t: (
                t.scheduled_time is None,
                t.scheduled_time or "",
                PRIORITY_ORDER[t.priority],
            ),
        )

        conflicts = self.detect_conflicts(all_tasks)

        scheduled: List[Task] = []
        skipped: List[Task] = []
        reasoning: dict = {}
        used_minutes = 0

        for task in sorted_tasks:
            if self.owner.can_fit(task, used_minutes):
                scheduled.append(task)
                used_minutes += task.duration_minutes
                reasoning[task.title] = (
                    f"Scheduled — {task.priority.value} priority, fits in remaining time "
                    f"({used_minutes}/{self.owner.available_minutes} min used)"
                )
            else:
                skipped.append(task)
                remaining = self.owner.available_minutes - used_minutes
                reasoning[task.title] = (
                    f"Skipped — needs {task.duration_minutes} min but only {remaining} min remaining"
                )

        return ScheduledPlan(
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            total_time=used_minutes,
            reasoning=reasoning,
            conflicts=conflicts,
        )
