from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# --- Setup Owner ---
owner = Owner(name="Jordan", available_time=120, preferences=["morning"])

# --- Setup Pets ---
buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
whiskers = Pet(name="Whiskers", species="Cat", breed="Tabby", age=5, special_needs=["daily medication"])

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Add Tasks to Buddy ---
buddy.add_task(Task(
    name="Morning Walk",
    task_type="walk",
    duration=30,
    priority=Priority.HIGH,
    time_of_day="morning",
    frequency="daily"
))

buddy.add_task(Task(
    name="Breakfast Feeding",
    task_type="feeding",
    duration=10,
    priority=Priority.HIGH,
    time_of_day="morning",
    frequency="daily"
))

buddy.add_task(Task(
    name="Fetch / Enrichment",
    task_type="enrichment",
    duration=20,
    priority=Priority.MEDIUM,
    time_of_day="afternoon",
    frequency="daily"
))

# --- Add Tasks to Whiskers ---
whiskers.add_task(Task(
    name="Administer Medication",
    task_type="meds",
    duration=5,
    priority=Priority.HIGH,
    time_of_day="morning",
    frequency="daily"
))

whiskers.add_task(Task(
    name="Brushing / Grooming",
    task_type="grooming",
    duration=15,
    priority=Priority.LOW,
    time_of_day="evening",
    frequency="weekly"
))

# --- Run Scheduler ---
scheduler = Scheduler(owner=owner)
scheduler.generate_plan()

# --- Print Results ---
print("=" * 50)
print("        TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.display())
print()
print("--- Scheduling Reasoning ---")
print(scheduler.get_reasoning())
print("=" * 50)
