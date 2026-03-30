from pawpal_system import Owner, Pet, Task, Scheduler, Priority

# --- Setup Owner ---
owner = Owner(name="Jordan", available_time=120, preferences=["morning"])

# --- Setup Pets ---
buddy = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
whiskers = Pet(name="Whiskers", species="Cat", breed="Tabby", age=5, special_needs=["daily medication"])

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Add Tasks OUT OF ORDER (intentionally scrambled times and priorities) ---
buddy.add_task(Task(
    name="Fetch / Enrichment",
    task_type="enrichment",
    duration=20,
    priority=Priority.MEDIUM,
    time_of_day="afternoon",
    start_time="14:00",
    frequency="daily"
))

buddy.add_task(Task(
    name="Breakfast Feeding",
    task_type="feeding",
    duration=10,
    priority=Priority.HIGH,
    time_of_day="morning",
    start_time="08:00",
    frequency="daily"
))

buddy.add_task(Task(
    name="Evening Walk",
    task_type="walk",
    duration=25,
    priority=Priority.MEDIUM,
    time_of_day="evening",
    start_time="17:30",
    frequency="daily"
))

buddy.add_task(Task(
    name="Morning Walk",
    task_type="walk",
    duration=30,
    priority=Priority.HIGH,
    time_of_day="morning",
    start_time="07:00",
    frequency="daily"
))

whiskers.add_task(Task(
    name="Brushing / Grooming",
    task_type="grooming",
    duration=15,
    priority=Priority.LOW,
    time_of_day="evening",
    start_time="18:00",
    frequency="weekly"
))

whiskers.add_task(Task(
    name="Afternoon Feeding",
    task_type="feeding",
    duration=10,
    priority=Priority.HIGH,
    time_of_day="afternoon",
    start_time="13:00",
    frequency="daily"
))

whiskers.add_task(Task(
    name="Administer Medication",
    task_type="meds",
    duration=5,
    priority=Priority.HIGH,
    time_of_day="morning",
    start_time="07:30",
    frequency="daily"
))

# --- Setup Scheduler ---
scheduler = Scheduler(owner=owner)

# -------------------------------------------------------
# TEST 1: Raw insertion order (before any sorting)
# -------------------------------------------------------
print("=" * 50)
print("  TEST 1: RAW INSERTION ORDER")
print("=" * 50)
all_tasks = owner.get_all_tasks()
for t in all_tasks:
    print(f"  {t.start_time or '??:??'}  [{t.priority.name}]  {t.name}")
print()

# -------------------------------------------------------
# TEST 2: _sort_by_time() — time only, ignores priority
# -------------------------------------------------------
print("=" * 50)
print("  TEST 2: SORTED BY TIME ONLY")
print("=" * 50)
by_time = scheduler._sort_by_time(all_tasks)
for t in by_time:
    print(f"  {t.start_time or '??:??'}  [{t.priority.name}]  {t.name}")
print()

# -------------------------------------------------------
# TEST 3: _sort_by_priority_and_time() — priority first, then time
# -------------------------------------------------------
print("=" * 50)
print("  TEST 3: SORTED BY PRIORITY + TIME")
print("=" * 50)
by_priority_time = scheduler._sort_by_priority_and_time(all_tasks)
for t in by_priority_time:
    print(f"  {t.start_time or '??:??'}  [{t.priority.name}]  {t.name}")
print()

# -------------------------------------------------------
# TEST 4: filter_tasks() — HIGH priority only
# -------------------------------------------------------
print("=" * 50)
print("  TEST 4: FILTER — HIGH PRIORITY ONLY")
print("=" * 50)
high_tasks = scheduler.filter_tasks(priority=Priority.HIGH)
for t in high_tasks:
    print(f"  [{t.priority.name}]  {t.name}  ({t.task_type}, {t.duration} min)")
print()

# -------------------------------------------------------
# TEST 5: filter_tasks() — by pet name
# -------------------------------------------------------
print("=" * 50)
print("  TEST 5: FILTER — WHISKERS' TASKS ONLY")
print("=" * 50)
whiskers_tasks = scheduler.filter_tasks(pet_name="Whiskers")
for t in whiskers_tasks:
    print(f"  {t.start_time}  {t.name}  | freq: {t.frequency}")
print()

# -------------------------------------------------------
# TEST 6: filter_tasks() — by task type
# -------------------------------------------------------
print("=" * 50)
print("  TEST 6: FILTER — FEEDING TASKS ONLY")
print("=" * 50)
feeding_tasks = scheduler.filter_tasks(task_type="feeding")
for t in feeding_tasks:
    print(f"  {t.start_time}  {t.name}  ({t.time_of_day})")
print()

# -------------------------------------------------------
# TEST 7: detect_conflicts() — no overlap expected yet
# -------------------------------------------------------
print("=" * 50)
print("  TEST 7A: CONFLICT DETECTION (clean)")
print("=" * 50)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for c in conflicts:
        print(f"  WARNING: {c}")
else:
    print("  No conflicts detected.")
print()

# Add a task that deliberately overlaps Morning Walk (07:00, 30 min → ends 07:30)
buddy.add_task(Task(
    name="Vet Call",
    task_type="meds",
    duration=20,
    priority=Priority.HIGH,
    time_of_day="morning",
    start_time="07:15",   # starts inside Morning Walk's window
    frequency="daily"
))

print("=" * 50)
print("  TEST 7B: CONFLICT DETECTION (with overlap)")
print("=" * 50)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for c in conflicts:
        print(f"  WARNING: {c}")
else:
    print("  No conflicts detected.")

# Remove the overlap task so it doesn't affect the schedule test
buddy.remove_task(buddy.tasks[-1].id)
print()

# -------------------------------------------------------
# TEST 8: generate_plan() — final sorted + filtered schedule
# -------------------------------------------------------
print("=" * 50)
print("  TEST 8: GENERATED SCHEDULE")
print("=" * 50)
scheduler.generate_plan()
print(scheduler.display())
print()
print("  Reasoning:")
print(scheduler.get_reasoning())
print()

# -------------------------------------------------------
# TEST 9: complete_task() — marks done, auto-renews next occurrence
# -------------------------------------------------------
print("=" * 50)
print("  TEST 9: RECURRING TASK RENEWAL")
print("=" * 50)

# Pick Morning Walk (daily) and Administer Medication (daily) to complete
targets = [t for t in owner.get_all_tasks() if t.name in ("Morning Walk", "Administer Medication")]

for task in targets:
    print(f"\n  Completing: '{task.name}' (frequency: {task.frequency})")
    print(f"    Before — completed: {task.completed}, next_due: {task.next_due or 'not set'}")
    renewed = scheduler.complete_task(task.id)
    print(f"    After  — completed: {task.completed}")
    if renewed:
        print(f"    Renewed task created: '{renewed.name}'")
        print(f"    New task next_due: {renewed.next_due}")
        print(f"    New task id (different): {renewed.id != task.id}")

print()
print("  All tasks for Buddy after renewal:")
for t in buddy.tasks:
    status = "DONE" if t.completed else "pending"
    print(f"    [{status}] {t.name} | next_due: {t.next_due or '—'}")

print()
print("  All tasks for Whiskers after renewal:")
for t in whiskers.tasks:
    status = "DONE" if t.completed else "pending"
    print(f"    [{status}] {t.name} | next_due: {t.next_due or '—'}")

print("=" * 50)
