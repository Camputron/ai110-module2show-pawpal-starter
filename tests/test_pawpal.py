import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


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


# --- Scheduler: priority and skipping ---

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


# --- Sorting ---

def test_sort_by_time_orders_correctly():
    """Tasks with scheduled_time should sort chronologically; unscheduled go last."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Afternoon walk", "walk", 20, Priority.LOW, scheduled_time="14:00"))
    pet.add_task(Task("Morning meds", "medication", 5, Priority.HIGH, scheduled_time="07:00"))
    pet.add_task(Task("Playtime", "enrichment", 15, Priority.LOW))  # no time

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(owner.get_all_tasks())
    assert sorted_tasks[0].title == "Morning meds"
    assert sorted_tasks[1].title == "Afternoon walk"
    assert sorted_tasks[2].title == "Playtime"


# --- Filtering ---

def test_filter_by_pet_name():
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    mochi.add_task(Task("Walk", "walk", 30, Priority.HIGH))
    luna.add_task(Task("Brushing", "grooming", 15, Priority.MEDIUM))

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    luna_only = scheduler.filter_tasks(owner.get_all_tasks(), pet_name="Luna")
    assert len(luna_only) == 1
    assert luna_only[0].title == "Brushing"


def test_filter_by_task_type():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 30, Priority.HIGH))
    pet.add_task(Task("Feeding", "feeding", 10, Priority.HIGH))
    pet.add_task(Task("Run", "walk", 20, Priority.MEDIUM))

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    walks = scheduler.filter_tasks(owner.get_all_tasks(), task_type="walk")
    assert len(walks) == 2


# --- Conflict detection ---

def test_detects_time_conflict():
    """Two tasks at the same time should produce a conflict warning."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 30, Priority.HIGH, scheduled_time="07:00"))
    pet.add_task(Task("Meds", "medication", 5, Priority.HIGH, scheduled_time="07:00"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.conflicts) == 1
    assert "07:00" in plan.conflicts[0]


def test_no_conflict_when_different_times():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 30, Priority.HIGH, scheduled_time="07:00"))
    pet.add_task(Task("Meds", "medication", 5, Priority.HIGH, scheduled_time="08:00"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.conflicts) == 0


# --- Recurring tasks ---

def test_daily_task_creates_next_occurrence():
    """Completing a daily task should produce a new task due tomorrow."""
    pet = Pet(name="Mochi", species="dog", age=3)
    today = date.today()
    walk = Task("Walk", "walk", 30, Priority.HIGH, frequency=Frequency.DAILY, due_date=today)
    pet.add_task(walk)

    pet.complete_task(walk)
    assert walk.completed is True
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_task_creates_next_occurrence():
    today = date.today()
    groom = Task("Grooming", "grooming", 30, Priority.MEDIUM, frequency=Frequency.WEEKLY, due_date=today)
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(groom)

    pet.complete_task(groom)
    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == today + timedelta(days=7)


def test_once_task_does_not_recur():
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task("Vet visit", "other", 60, Priority.HIGH, frequency=Frequency.ONCE)
    pet.add_task(task)

    pet.complete_task(task)
    assert len(pet.tasks) == 1  # no new task created


# --- Edge cases ---

def test_schedule_with_no_tasks():
    """An owner with pets but no tasks should get an empty schedule."""
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(Pet(name="Mochi", species="dog", age=3))

    plan = Scheduler(owner).generate_schedule()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []
    assert plan.total_time == 0
    assert plan.conflicts == []


def test_schedule_with_no_pets():
    """An owner with no pets should get an empty schedule."""
    owner = Owner(name="Jordan", available_minutes=60)
    plan = Scheduler(owner).generate_schedule()
    assert plan.scheduled_tasks == []
    assert plan.total_time == 0


def test_schedule_zero_available_minutes():
    """With zero available time, all tasks should be skipped."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 10, Priority.HIGH))

    owner = Owner(name="Jordan", available_minutes=0)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.scheduled_tasks) == 0
    assert len(plan.skipped_tasks) == 1


def test_task_exactly_fills_remaining_time():
    """A task that exactly matches remaining time should be scheduled, not skipped."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 60, Priority.HIGH))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.scheduled_tasks) == 1
    assert plan.total_time == 60


def test_three_way_time_conflict():
    """Three tasks at the same time should all appear in the conflict warning."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 10, Priority.HIGH, scheduled_time="08:00"))
    pet.add_task(Task("Feed", "feeding", 10, Priority.HIGH, scheduled_time="08:00"))
    pet.add_task(Task("Meds", "medication", 5, Priority.HIGH, scheduled_time="08:00"))

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert len(plan.conflicts) == 1
    assert "Walk" in plan.conflicts[0]
    assert "Feed" in plan.conflicts[0]
    assert "Meds" in plan.conflicts[0]


def test_all_tasks_completed_returns_empty_schedule():
    """If every task is already completed, the schedule should be empty."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 30, Priority.HIGH, completed=True))
    pet.add_task(Task("Feed", "feeding", 10, Priority.HIGH, completed=True))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    assert plan.scheduled_tasks == []
    assert plan.total_time == 0


def test_pet_summary_with_special_needs():
    pet = Pet(name="Luna", species="cat", age=5, special_needs=["thyroid medication", "soft food"])
    assert "thyroid medication" in pet.summary()
    assert "soft food" in pet.summary()


def test_pet_summary_without_special_needs():
    pet = Pet(name="Mochi", species="dog", age=3)
    summary = pet.summary()
    assert "special needs" not in summary
    assert "Mochi" in summary


def test_display_output_includes_scheduled_tasks():
    """ScheduledPlan.display() should include all scheduled task titles."""
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", "walk", 30, Priority.HIGH))
    pet.add_task(Task("Feed", "feeding", 10, Priority.MEDIUM))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_schedule()
    output = plan.display()
    assert "Walk" in output
    assert "Feed" in output
    assert "Total time: 40 min" in output
