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
    time_of_day = st.selectbox("Time of day (optional)", ["none", "morning", "afternoon", "evening"])

    if st.button("Add Task"):
        task = Task(
            name=task_title,
            task_type=task_type,
            duration=int(duration),
            priority=Priority[priority],
            time_of_day=None if time_of_day == "none" else time_of_day,
        )
        st.session_state.current_pet.add_task(task)
        st.success(f"Added task: {task_title}")

    # Show current tasks for the pet
    tasks = st.session_state.current_pet.tasks
    if tasks:
        st.write(f"Tasks for **{st.session_state.current_pet.name}**:")
        st.table([
            {
                "Task": t.name,
                "Type": t.task_type,
                "Duration (min)": t.duration,
                "Priority": t.priority.name,
                "Time of Day": t.time_of_day or "—",
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
        st.success("Schedule generated!")
        st.text(st.session_state.scheduler.display())
        with st.expander("Scheduling Reasoning"):
            st.text(st.session_state.scheduler.get_reasoning())
