from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    task_type: str
    duration_minutes: int
    priority: Priority
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == Priority.HIGH

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


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
    """The output of the scheduler — an ordered plan with reasoning."""

    def __init__(
        self,
        scheduled_tasks: List[Task],
        skipped_tasks: List[Task],
        total_time: int,
        reasoning: dict,
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_time = total_time
        self.reasoning = reasoning

    def display(self) -> str:
        """Format the plan as a readable string for terminal or UI output."""
        lines = ["=== Today's Schedule ===\n"]

        if self.scheduled_tasks:
            for i, task in enumerate(self.scheduled_tasks, 1):
                reason = self.reasoning.get(task.title, "")
                lines.append(f"  {i}. {task.title} ({task.duration_minutes} min) [{task.priority.value}]")
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

    def generate_schedule(self) -> ScheduledPlan:
        """Sort all tasks by priority, greedily schedule what fits, and record reasoning."""
        all_tasks = self.owner.get_all_tasks()
        sorted_tasks = sorted(all_tasks, key=lambda t: PRIORITY_ORDER[t.priority])

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
        )
