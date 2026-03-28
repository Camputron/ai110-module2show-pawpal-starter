from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5, special_needs=["thyroid medication"])

# --- Tasks added out of order (to test sorting) ---
mochi.add_task(Task("Enrichment toy", "enrichment", 20, Priority.LOW, scheduled_time="14:00"))
mochi.add_task(Task("Morning walk", "walk", 30, Priority.HIGH, scheduled_time="07:00", frequency=Frequency.DAILY, due_date=date.today()))
mochi.add_task(Task("Breakfast feeding", "feeding", 10, Priority.HIGH, scheduled_time="07:30"))

luna.add_task(Task("Thyroid medication", "medication", 5, Priority.HIGH, scheduled_time="07:00"))  # conflicts with Mochi's walk!
luna.add_task(Task("Brushing", "grooming", 15, Priority.MEDIUM, scheduled_time="10:00"))
luna.add_task(Task("Playtime", "enrichment", 25, Priority.LOW))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# --- 1. Generate schedule (with conflict detection) ---
plan = scheduler.generate_schedule()
print(plan.display())

# --- 2. Sort by time ---
print("\n\n=== Tasks Sorted by Time ===")
all_tasks = owner.get_all_tasks()
for t in scheduler.sort_by_time(all_tasks):
    time_str = t.scheduled_time or "unscheduled"
    print(f"  {time_str} — {t.title} [{t.priority.value}]")

# --- 3. Filter by pet ---
print("\n=== Luna's Tasks Only ===")
luna_tasks = scheduler.filter_tasks(all_tasks, pet_name="Luna")
for t in luna_tasks:
    print(f"  • {t.title} ({t.duration_minutes} min)")

# --- 4. Filter by type ---
print("\n=== All Enrichment Tasks ===")
enrichment = scheduler.filter_tasks(all_tasks, task_type="enrichment")
for t in enrichment:
    print(f"  • {t.title} — {t.duration_minutes} min")

# --- 5. Recurring task demo ---
print("\n=== Recurring Task Demo ===")
walk = mochi.tasks[1]  # Morning walk (daily)
print(f"Completing '{walk.title}' (due {walk.due_date})...")
mochi.complete_task(walk)
next_walk = [t for t in mochi.tasks if t.title == "Morning walk" and not t.completed][0]
print(f"Next occurrence auto-created: due {next_walk.due_date}")
