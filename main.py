from pawpal_system import Task, Pet, Owner, Scheduler, Priority

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5, special_needs=["thyroid medication"])

# --- Tasks for Mochi ---
mochi.add_task(Task("Morning walk", "walk", 30, Priority.HIGH))
mochi.add_task(Task("Breakfast feeding", "feeding", 10, Priority.HIGH))
mochi.add_task(Task("Enrichment toy", "enrichment", 20, Priority.LOW))

# --- Tasks for Luna ---
luna.add_task(Task("Thyroid medication", "medication", 5, Priority.HIGH))
luna.add_task(Task("Brushing", "grooming", 15, Priority.MEDIUM))
luna.add_task(Task("Playtime", "enrichment", 25, Priority.LOW))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Generate and display schedule ---
scheduler = Scheduler(owner)
plan = scheduler.generate_schedule()
print(plan.display())
