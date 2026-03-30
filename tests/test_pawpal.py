import datetime
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, Priority


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_task(name, task_type="walk", duration=30, priority=Priority.MEDIUM,
              time_of_day=None, start_time=None, frequency="daily"):
    return Task(
        name=name,
        task_type=task_type,
        duration=duration,
        priority=priority,
        time_of_day=time_of_day,
        start_time=start_time,
        frequency=frequency,
    )


def make_scheduler(available_time=240, preferences=None):
    owner = Owner("Test Owner", available_time=available_time, preferences=preferences or [])
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    return scheduler, pet


# ─── Existing tests (kept) ─────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """Calling mark_complete() should set the task's completed flag to True."""
    task = make_task("Morning Walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list length by one."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task("Breakfast Feeding", task_type="feeding", duration=10))
    assert len(pet.tasks) == 1


# ─── SORTING CORRECTNESS ──────────────────────────────────────────────────────

def test_sort_priority_high_before_low():
    """HIGH priority tasks must appear before LOW priority tasks."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("Low Task",  priority=Priority.LOW,  start_time="10:00"))
    pet.add_task(make_task("High Task", priority=Priority.HIGH, start_time="11:00"))
    pet.add_task(make_task("Med Task",  priority=Priority.MEDIUM, start_time="09:00"))

    scheduler.generate_plan()
    priorities = [t.priority for t in scheduler.scheduled_tasks]
    assert priorities == sorted(priorities, key=lambda p: p.value)


def test_sort_time_tiebreaker_within_same_priority():
    """Tasks with the same priority should be ordered by start_time ascending."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("Later",   priority=Priority.MEDIUM, start_time="10:00"))
    pet.add_task(make_task("Earlier", priority=Priority.MEDIUM, start_time="08:00"))

    scheduler.generate_plan()
    names = [t.name for t in scheduler.scheduled_tasks]
    assert names.index("Earlier") < names.index("Later")


def test_sort_tasks_without_start_time_placed_last():
    """Within the same priority, tasks with no start_time should follow timed tasks."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("No Time",   priority=Priority.MEDIUM, start_time=None))
    pet.add_task(make_task("Has Time",  priority=Priority.MEDIUM, start_time="09:00"))

    scheduler.generate_plan()
    names = [t.name for t in scheduler.scheduled_tasks]
    assert names.index("Has Time") < names.index("No Time")


def test_sort_chronological_order_multiple_tasks():
    """A mixed set of tasks should come out in strict chronological order when priorities match."""
    scheduler, pet = make_scheduler()
    times = ["14:00", "07:30", "11:15", "09:00"]
    for t in times:
        pet.add_task(make_task(f"Task {t}", priority=Priority.MEDIUM, start_time=t))

    scheduler.generate_plan()
    start_times = [task.start_time for task in scheduler.scheduled_tasks]
    assert start_times == sorted(start_times)


# ─── RECURRENCE LOGIC ─────────────────────────────────────────────────────────

def test_complete_daily_task_creates_renewal():
    """Completing a daily task should add a new task to the pet's task list."""
    scheduler, pet = make_scheduler()
    task = make_task("Daily Walk", frequency="daily")
    pet.add_task(task)

    original_count = len(pet.tasks)
    scheduler.complete_task(task.id)
    assert len(pet.tasks) == original_count + 1


def test_complete_daily_task_next_due_is_tomorrow():
    """The renewed task's next_due should be exactly one day from today."""
    scheduler, pet = make_scheduler()
    task = make_task("Daily Walk", frequency="daily")
    pet.add_task(task)

    renewed = scheduler.complete_task(task.id)
    tomorrow = str(datetime.date.today() + datetime.timedelta(days=1))
    assert renewed is not None
    assert renewed.next_due == tomorrow


def test_complete_weekly_task_next_due_is_seven_days():
    """The renewed task's next_due should be exactly seven days from today."""
    scheduler, pet = make_scheduler()
    task = make_task("Weekly Bath", frequency="weekly")
    pet.add_task(task)

    renewed = scheduler.complete_task(task.id)
    next_week = str(datetime.date.today() + datetime.timedelta(weeks=1))
    assert renewed is not None
    assert renewed.next_due == next_week


def test_complete_as_needed_task_no_renewal():
    """Completing an as-needed task should NOT create a follow-up task."""
    scheduler, pet = make_scheduler()
    task = make_task("Vet Visit", frequency="as-needed")
    pet.add_task(task)

    original_count = len(pet.tasks)
    renewed = scheduler.complete_task(task.id)
    assert renewed is None
    assert len(pet.tasks) == original_count   # no new task added


def test_renewal_preserves_original_fields():
    """The renewed task should carry over name, duration, and priority unchanged."""
    scheduler, pet = make_scheduler()
    task = make_task("Morning Run", task_type="exercise", duration=45,
                     priority=Priority.HIGH, frequency="daily")
    pet.add_task(task)

    renewed = scheduler.complete_task(task.id)
    assert renewed.name == task.name
    assert renewed.duration == task.duration
    assert renewed.priority == task.priority
    assert renewed.task_type == task.task_type


def test_completed_task_excluded_from_plan():
    """A completed task should not appear in the generated plan."""
    scheduler, pet = make_scheduler()
    task = make_task("Done Task")
    task.mark_complete()
    pet.add_task(task)

    scheduler.generate_plan()
    assert task not in scheduler.scheduled_tasks


# ─── CONFLICT DETECTION ───────────────────────────────────────────────────────

def test_conflict_time_overlap_detected():
    """Two tasks whose windows overlap should produce an overlap conflict."""
    scheduler, pet = make_scheduler()
    # Task A: 09:00 → 09:45, Task B: 09:30 → 10:00  (15-min overlap)
    pet.add_task(make_task("Task A", start_time="09:00", duration=45))
    pet.add_task(make_task("Task B", start_time="09:30", duration=30))

    conflicts = scheduler.detect_conflicts()
    assert any("Overlap" in c for c in conflicts)


def test_conflict_no_overlap_when_tasks_touch():
    """Tasks that share an endpoint but do not overlap should NOT be flagged."""
    scheduler, pet = make_scheduler()
    # Task A ends at 10:00, Task B starts at 10:00 — touching, not overlapping
    pet.add_task(make_task("Task A", start_time="09:00", duration=60))
    pet.add_task(make_task("Task B", start_time="10:00", duration=30))

    conflicts = scheduler.detect_conflicts()
    overlap_conflicts = [c for c in conflicts if "Overlap" in c]
    assert len(overlap_conflicts) == 0


def test_conflict_slot_overload_detected():
    """Tasks in the same slot exceeding 120 min should trigger a time-overload conflict."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("A", time_of_day="morning", duration=70))
    pet.add_task(make_task("B", time_of_day="morning", duration=60))  # total = 130 min

    conflicts = scheduler.detect_conflicts()
    assert any("overload" in c.lower() for c in conflicts)


def test_conflict_no_overload_at_exactly_120_min():
    """Tasks totaling exactly 120 min in a slot should NOT trigger an overload."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("A", time_of_day="morning", duration=60))
    pet.add_task(make_task("B", time_of_day="morning", duration=60))  # total = 120 min

    conflicts = scheduler.detect_conflicts()
    overload_conflicts = [c for c in conflicts if "overload" in c.lower()]
    assert len(overload_conflicts) == 0


def test_conflict_duplicate_task_type_in_same_slot():
    """Two tasks of the same type in the same slot should NOT be flagged.
    A pet can legitimately have two walks in one slot (morning + after breakfast).
    Timing conflicts are caught by the overlap check instead.
    """
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("Walk 1", task_type="walk", time_of_day="morning", duration=30))
    pet.add_task(make_task("Walk 2", task_type="walk", time_of_day="morning", duration=30))

    conflicts = scheduler.detect_conflicts()
    assert not any("Duplicate" in c for c in conflicts)


def test_conflict_same_type_different_slots_no_conflict():
    """Duplicate task types in different slots should NOT produce a conflict."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("Morning Walk", task_type="walk", time_of_day="morning",  duration=30))
    pet.add_task(make_task("Evening Walk", task_type="walk", time_of_day="evening",  duration=30))

    conflicts = scheduler.detect_conflicts()
    duplicate_conflicts = [c for c in conflicts if "Duplicate" in c]
    assert len(duplicate_conflicts) == 0


def test_conflict_no_conflicts_for_clean_schedule():
    """A well-spaced schedule with no duplicates or overloads should return no conflicts."""
    scheduler, pet = make_scheduler()
    pet.add_task(make_task("Walk",    task_type="walk",    time_of_day="morning",   start_time="08:00", duration=30))
    pet.add_task(make_task("Feeding", task_type="feeding", time_of_day="afternoon", start_time="12:00", duration=15))

    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


# ─── AVAILABLE TIME BUDGET ────────────────────────────────────────────────────

def test_plan_skips_tasks_exceeding_budget():
    """Tasks that would push total duration past available_time should be skipped."""
    scheduler, pet = make_scheduler(available_time=50)
    pet.add_task(make_task("Task A", priority=Priority.HIGH,   duration=30))
    pet.add_task(make_task("Task B", priority=Priority.MEDIUM, duration=30))  # would exceed 50

    scheduler.generate_plan()
    assert len(scheduler.scheduled_tasks) == 1
    assert scheduler.scheduled_tasks[0].name == "Task A"


def test_plan_zero_budget_no_tasks_scheduled():
    """With zero available time, no tasks should be scheduled."""
    scheduler, pet = make_scheduler(available_time=0)
    pet.add_task(make_task("Any Task", duration=10))

    scheduler.generate_plan()
    assert scheduler.scheduled_tasks == []


def test_plan_exact_budget_all_tasks_included():
    """Tasks whose combined duration exactly equals available_time should all be included."""
    scheduler, pet = make_scheduler(available_time=60)
    pet.add_task(make_task("Task A", priority=Priority.HIGH,   duration=30))
    pet.add_task(make_task("Task B", priority=Priority.MEDIUM, duration=30))

    scheduler.generate_plan()
    assert len(scheduler.scheduled_tasks) == 2
    assert scheduler.total_duration == 60
