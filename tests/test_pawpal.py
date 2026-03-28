import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Priority


# --- Task tests ---

def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = Task("Morning walk", "walk", 30, Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_is_high_priority_true_for_high():
    task = Task("Medication", "medication", 5, Priority.HIGH)
    assert task.is_high_priority() is True


def test_is_high_priority_false_for_low():
    task = Task("Playtime", "enrichment", 20, Priority.LOW)
    assert task.is_high_priority() is False


# --- Pet tests ---

def test_add_task_increases_task_count():
    """Adding a task to a pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task("Walk", "walk", 20, Priority.MEDIUM))
    assert len(pet.tasks) == 1


def test_add_multiple_tasks():
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(Task("Feeding", "feeding", 10, Priority.HIGH))
    pet.add_task(Task("Brushing", "grooming", 15, Priority.MEDIUM))
    assert len(pet.tasks) == 2


# --- Owner tests ---

def test_get_all_tasks_returns_incomplete_only():
    """get_all_tasks should exclude completed tasks."""
    pet = Pet(name="Mochi", species="dog", age=2)
    done = Task("Old walk", "walk", 20, Priority.LOW, completed=True)
    pending = Task("Feeding", "feeding", 10, Priority.HIGH)
    pet.add_task(done)
    pet.add_task(pending)

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    tasks = owner.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Feeding"


def test_can_fit_true_when_time_available():
    owner = Owner(name="Jordan", available_minutes=60)
    task = Task("Walk", "walk", 30, Priority.HIGH)
    assert owner.can_fit(task, used_minutes=20) is True


def test_can_fit_false_when_no_time():
    owner = Owner(name="Jordan", available_minutes=60)
    task = Task("Long walk", "walk", 45, Priority.HIGH)
    assert owner.can_fit(task, used_minutes=30) is False


# --- Scheduler tests ---

def test_schedule_respects_priority_order():
    """High priority tasks should appear before lower priority ones."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Playtime", "enrichment", 10, Priority.LOW))
    pet.add_task(Task("Medication", "medication", 5, Priority.HIGH))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert plan.scheduled_tasks[0].title == "Medication"


def test_schedule_skips_tasks_that_dont_fit():
    """Tasks exceeding remaining time should land in skipped_tasks."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Big walk", "walk", 50, Priority.HIGH))
    pet.add_task(Task("Long run", "walk", 60, Priority.HIGH))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.skipped_tasks) == 1
    assert plan.skipped_tasks[0].title == "Long run"
