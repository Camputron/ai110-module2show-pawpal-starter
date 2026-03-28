import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

DATA_FILE = "data.json"

TASK_EMOJIS = {
    "walk": "🚶",
    "feeding": "🍽️",
    "medication": "💊",
    "grooming": "✂️",
    "enrichment": "🧸",
    "other": "📋",
}

PRIORITY_COLORS = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}


def save_owner():
    """Persist owner data to JSON."""
    st.session_state.owner.save_to_json(DATA_FILE)


st.title("🐾 PawPal+")
st.caption("Your smart pet care scheduling assistant")

# --- Session State: load from JSON or create fresh ---
if "owner" not in st.session_state:
    loaded = Owner.load_from_json(DATA_FILE)
    st.session_state.owner = loaded if loaded else Owner(name="", available_minutes=60)

owner = st.session_state.owner

# --- Owner Setup ---
st.subheader("👤 Owner Info")
col_name, col_time = st.columns(2)
with col_name:
    owner.name = st.text_input("Owner name", value=owner.name or "Jordan")
with col_time:
    owner.available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=480, value=owner.available_minutes
    )

st.divider()

# --- Add a Pet ---
st.subheader("🐾 Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        pet_name = st.text_input("Pet name")
    with pcol2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with pcol3:
        age = st.number_input("Age", min_value=0, max_value=30, value=1)
    special_needs = st.text_input("Special needs (comma-separated, optional)")

    if st.form_submit_button("Add Pet"):
        if pet_name.strip():
            needs = [s.strip() for s in special_needs.split(",") if s.strip()] if special_needs else []
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age), special_needs=needs))
            save_owner()
            st.success(f"Added {pet_name}!")
        else:
            st.warning("Please enter a pet name.")

# Show current pets
if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        species_emoji = {"dog": "🐕", "cat": "🐈", "other": "🐾"}.get(pet.species, "🐾")
        st.write(f"{species_emoji} {pet.summary()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a Task to a Pet ---
if owner.pets:
    st.subheader("📝 Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        pet_choice = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            task_title = st.text_input("Task title")
        with tcol2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with tcol3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        tcol4, tcol5, tcol6 = st.columns(3)
        with tcol4:
            task_type = st.selectbox("Type", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])
        with tcol5:
            scheduled_time = st.text_input("Scheduled time (HH:MM, optional)")
        with tcol6:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

        if st.form_submit_button("Add Task"):
            if task_title.strip():
                target_pet = next(p for p in owner.pets if p.name == pet_choice)
                time_val = scheduled_time.strip() if scheduled_time.strip() else None
                target_pet.add_task(
                    Task(
                        title=task_title.strip(),
                        task_type=task_type,
                        duration_minutes=int(duration),
                        priority=Priority(priority),
                        scheduled_time=time_val,
                        frequency=Frequency(frequency),
                    )
                )
                save_owner()
                st.success(f"Added '{task_title}' to {pet_choice}!")
            else:
                st.warning("Please enter a task title.")

    # --- Current tasks table ---
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.markdown("**All pending tasks:**")
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time(all_tasks)
        task_data = [
            {
                "": TASK_EMOJIS.get(t.task_type, "📋"),
                "Time": t.scheduled_time or "—",
                "Task": t.title,
                "Duration": f"{t.duration_minutes} min",
                "Priority": f"{PRIORITY_COLORS[t.priority.value]} {t.priority.value}",
                "Freq": t.frequency.value,
            }
            for t in sorted_tasks
        ]
        st.table(task_data)

    # --- Filter tasks ---
    if len(owner.pets) > 1:
        st.markdown("**Filter by pet:**")
        filter_pet = st.selectbox("Select pet to filter", ["All"] + [p.name for p in owner.pets])
        if filter_pet != "All":
            filtered = scheduler.filter_tasks(all_tasks, pet_name=filter_pet)
            if filtered:
                st.table([
                    {
                        "": TASK_EMOJIS.get(t.task_type, "📋"),
                        "Task": t.title,
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": f"{PRIORITY_COLORS[t.priority.value]} {t.priority.value}",
                    }
                    for t in filtered
                ])
            else:
                st.info(f"No pending tasks for {filter_pet}.")

st.divider()

# --- Generate Schedule ---
st.subheader("📅 Build Schedule")

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("No tasks to schedule. Add pets and tasks first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_schedule()

        # Conflicts
        if plan.conflicts:
            st.error("**⚠️ Scheduling Conflicts Detected**")
            for c in plan.conflicts:
                st.warning(c)

        # Scheduled tasks
        st.markdown("### ✅ Scheduled")
        if plan.scheduled_tasks:
            for i, task in enumerate(plan.scheduled_tasks, 1):
                reason = plan.reasoning.get(task.title, "")
                emoji = TASK_EMOJIS.get(task.task_type, "📋")
                pri = PRIORITY_COLORS[task.priority.value]
                time_str = f" @ {task.scheduled_time}" if task.scheduled_time else ""
                freq_str = f" 🔁 {task.frequency.value}" if task.frequency != Frequency.ONCE else ""
                st.markdown(
                    f"**{i}. {emoji} {task.title}**{time_str} — "
                    f"{task.duration_minutes} min | {pri} {task.priority.value}{freq_str}"
                )
                st.caption(reason)
        else:
            st.info("No tasks could be scheduled.")

        # Summary metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Scheduled", f"{len(plan.scheduled_tasks)} tasks")
        col_m2.metric("Time used", f"{plan.total_time} / {owner.available_minutes} min")
        col_m3.metric("Skipped", f"{len(plan.skipped_tasks)} tasks")

        # Skipped tasks
        if plan.skipped_tasks:
            st.markdown("### ⏭️ Skipped")
            for task in plan.skipped_tasks:
                reason = plan.reasoning.get(task.title, "")
                emoji = TASK_EMOJIS.get(task.task_type, "📋")
                st.markdown(f"• {emoji} **{task.title}** — {task.duration_minutes} min")
                st.caption(reason)

        save_owner()
