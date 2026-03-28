import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session State: persist the Owner across reruns ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="", available_minutes=60)

owner = st.session_state.owner

# --- Owner Setup ---
st.subheader("Owner Info")
col_name, col_time = st.columns(2)
with col_name:
    owner.name = st.text_input("Owner name", value=owner.name or "Jordan")
with col_time:
    owner.available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=480, value=owner.available_minutes
    )

st.divider()

# --- Add a Pet ---
st.subheader("Add a Pet")
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
            st.success(f"Added {pet_name}!")
        else:
            st.warning("Please enter a pet name.")

# Show current pets
if owner.pets:
    st.markdown("**Your pets:**")
    for pet in owner.pets:
        st.write(f"• {pet.summary()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a Task to a Pet ---
if owner.pets:
    st.subheader("Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        pet_choice = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            task_title = st.text_input("Task title")
        with tcol2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with tcol3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        task_type = st.selectbox("Type", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])

        if st.form_submit_button("Add Task"):
            if task_title.strip():
                target_pet = next(p for p in owner.pets if p.name == pet_choice)
                target_pet.add_task(
                    Task(
                        title=task_title.strip(),
                        task_type=task_type,
                        duration_minutes=int(duration),
                        priority=Priority(priority),
                    )
                )
                st.success(f"Added '{task_title}' to {pet_choice}!")
            else:
                st.warning("Please enter a task title.")

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("No tasks to schedule. Add pets and tasks first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_schedule()

        # Conflicts
        if plan.conflicts:
            for c in plan.conflicts:
                st.warning(f"⚠️ {c}")

        # Scheduled tasks
        st.markdown("### ✅ Scheduled")
        for i, task in enumerate(plan.scheduled_tasks, 1):
            reason = plan.reasoning.get(task.title, "")
            st.markdown(f"**{i}. {task.title}** — {task.duration_minutes} min [{task.priority.value}]")
            st.caption(reason)

        st.metric("Total scheduled time", f"{plan.total_time} / {owner.available_minutes} min")

        # Skipped tasks
        if plan.skipped_tasks:
            st.markdown("### ⏭️ Skipped")
            for task in plan.skipped_tasks:
                reason = plan.reasoning.get(task.title, "")
                st.markdown(f"• **{task.title}** — {task.duration_minutes} min")
                st.caption(reason)
