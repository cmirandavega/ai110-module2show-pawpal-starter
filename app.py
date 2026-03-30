import datetime
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session state initialisation ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False


def fmt_ampm(time_str: str) -> str:
    """Convert 24-hour 'HH:MM' to '9:00 AM' display format."""
    if not time_str:
        return "—"
    h, m = map(int, time_str.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"


def slot_from_hour(hour: int) -> str:
    """Derive morning / afternoon / evening from a 24-hour value."""
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


# --- Section 1: Owner + Pet Setup ---
st.subheader("Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=120)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Mixed")
    age = st.number_input("Pet age", min_value=0, max_value=30, value=2)

if st.button("Save Owner & Pet"):
    pet = Pet(name=pet_name, species=species, breed=breed, age=int(age))
    owner = Owner(name=owner_name, available_time=int(available_time))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.current_pet = pet
    st.session_state.scheduler = Scheduler(owner=owner)
    st.session_state.plan_generated = False
    st.success(f"Saved! Owner: {owner_name} | Pet: {pet_name} ({species})")

st.divider()

# --- Section 2: Add Tasks ---
st.subheader("Add a Task")

if st.session_state.current_pet is None:
    st.info("Save an owner and pet above before adding tasks.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task name", value="Morning walk")
    with col2:
        task_type = st.selectbox("Type", ["walk", "feeding", "meds", "grooming", "enrichment"])
    with col3:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"], index=0)

    col5, col6 = st.columns(2)
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col6:
        use_start_time = st.checkbox("Set a start time?", value=True)

    picked_time = None
    if use_start_time:
        picked_time = st.time_input("Start time", value=datetime.time(9, 0), step=300)

    if st.button("Add Task"):
        if picked_time is not None:
            start_str = picked_time.strftime("%H:%M")
            time_of_day = slot_from_hour(picked_time.hour)
        else:
            start_str = None
            time_of_day = None

        task = Task(
            name=task_title,
            task_type=task_type,
            duration=int(duration),
            priority=Priority[priority],
            time_of_day=time_of_day,
            start_time=start_str,
            frequency=frequency,
        )

        # Tentative add: check whether this task introduces any new conflicts
        conflicts_before = set(st.session_state.scheduler.detect_conflicts())
        st.session_state.current_pet.add_task(task)
        conflicts_after = set(st.session_state.scheduler.detect_conflicts())
        new_conflicts = conflicts_after - conflicts_before

        if new_conflicts:
            # Roll back — remove the task we just added
            st.session_state.current_pet.remove_task(task.id)
            st.error(f"❌ **{task_title}** was not added due to a scheduling conflict:")
            for c in new_conflicts:
                st.warning(f"• {c}")
        else:
            time_label = fmt_ampm(start_str) if start_str else "no start time"
            st.success(f"Added: **{task_title}** ({priority}, {duration} min) at {time_label}")

    # --- Task list with conflict warnings ---
    tasks = st.session_state.current_pet.tasks
    if tasks:
        st.write(f"**Tasks for {st.session_state.current_pet.name}** ({len(tasks)} total)")

        conflicts = st.session_state.scheduler.detect_conflicts()
        if conflicts:
            st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
            for c in conflicts:
                st.warning(f"• {c}")
        else:
            st.success("No scheduling conflicts detected.")

        priority_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        st.table([
            {
                "": priority_color.get(t.priority.name, ""),
                "Task": t.name,
                "Type": t.task_type,
                "Duration (min)": t.duration,
                "Priority": t.priority.name,
                "Start Time": fmt_ampm(t.start_time),
                "Frequency": t.frequency,
                "Status": "✅ Done" if t.completed else "Pending",
            }
            for t in tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Section 3: Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate Schedule"):
    if st.session_state.scheduler is None:
        st.warning("Save an owner and pet first.")
    elif not st.session_state.current_pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        st.session_state.scheduler.generate_plan()
        st.session_state.plan_generated = True

# --- Schedule display (persists across reruns) ---
if st.session_state.plan_generated and st.session_state.scheduler:
    scheduler = st.session_state.scheduler
    scheduled = scheduler.scheduled_tasks
    skipped_count = len(st.session_state.current_pet.tasks) - len(scheduled)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks Scheduled", len(scheduled))
    col2.metric("Total Time (min)", scheduler.total_duration)
    col3.metric("Tasks Skipped", skipped_count)

    if scheduled:
        st.success(f"Schedule generated for **{st.session_state.owner.name}**")
        priority_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        st.table([
            {
                "": priority_color.get(t.priority.name, ""),
                "Task": t.name,
                "Type": t.task_type,
                "Priority": t.priority.name,
                "Duration (min)": t.duration,
                "Start Time": fmt_ampm(t.start_time),
                "Frequency": t.frequency,
                "Status": "✅ Done" if t.completed else "⬜ Pending",
            }
            for t in scheduled
        ])
    else:
        st.warning("No tasks fit within your available time.")

    with st.expander("Scheduling Reasoning"):
        for line in scheduler.reasoning:
            if "Skipped" in line:
                st.warning(f"• {line}")
            else:
                st.success(f"• {line}")

    conflicts = scheduler.detect_conflicts()
    with st.expander(f"Conflict Report ({len(conflicts)} found)"):
        if conflicts:
            for c in conflicts:
                st.warning(f"⚠️ {c}")
        else:
            st.success("No conflicts found in the current task list.")

    st.divider()
    st.subheader("Mark a Task Complete")
    incomplete = [t for t in scheduled if not t.completed]
    if incomplete:
        task_options = {f"{t.name} ({fmt_ampm(t.start_time)})": t.id for t in incomplete}
        chosen = st.selectbox("Select task to complete", list(task_options.keys()))
        if st.button("Mark Complete"):
            renewed = scheduler.complete_task(task_options[chosen])
            if renewed:
                st.session_state.renewal_msg = f"↻ Next occurrence scheduled for {renewed.next_due}"
            st.rerun()

    if "renewal_msg" in st.session_state:
        st.info(st.session_state.renewal_msg)
        del st.session_state.renewal_msg
    else:
        st.success("All tasks in this plan are complete!")
