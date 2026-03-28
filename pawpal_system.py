from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    task_type: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    completed: bool = False

    def is_high_priority(self) -> bool:
        pass

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: List[str] = field(default_factory=list)

    def summary(self) -> str:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int

    def can_fit(self, task: Task) -> bool:
        pass


class ScheduledPlan:
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
        pass


class Scheduler:
    def __init__(self, tasks: List[Task], owner: Owner, pet: Pet):
        self.tasks = tasks
        self.owner = owner
        self.pet = pet

    def generate_schedule(self) -> ScheduledPlan:
        pass

    def explain_plan(self, plan: ScheduledPlan) -> dict:
        pass
