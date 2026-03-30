from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from collections import defaultdict
import datetime
import uuid

# Minutes available per time-of-day slot (used for conflict detection)
TIME_SLOT_BUDGET = {"morning": 120, "afternoon": 120, "evening": 120}


class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    """Represents a single pet care activity."""
    name: str
    task_type: str
    duration: int           # in minutes
    priority: Priority
    time_of_day: Optional[str] = None   # "morning", "afternoon", "evening"
    start_time: Optional[str] = None    # "HH:MM" format, e.g. "09:30"
    completed: bool = False
    frequency: str = "daily"            # daily, weekly, as-needed
    next_due: Optional[str] = None      # "YYYY-MM-DD" date of next occurrence
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def edit(self, field_name: str, value) -> None:
        """Update any attribute by name. Raises AttributeError for unknown fields."""
        if not hasattr(self, field_name):
            raise AttributeError(f"Task has no attribute '{field_name}'")
        setattr(self, field_name, value)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def renew(self) -> Optional["Task"]:
        """Return a new Task instance for the next occurrence, or None for as-needed tasks."""
        today = datetime.date.today()
        if self.frequency == "daily":
            next_date = today + datetime.timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = today + datetime.timedelta(weeks=1)
        else:
            return None  # as-needed tasks are not auto-renewed
        return Task(
            name=self.name,
            task_type=self.task_type,
            duration=self.duration,
            priority=self.priority,
            time_of_day=self.time_of_day,
            start_time=self.start_time,
            frequency=self.frequency,
            next_due=str(next_date),
        )

    def get_summary(self) -> str:
        """Return a readable one-line description of the task."""
        status = "Done" if self.completed else "Pending"
        time_label = f" ({self.time_of_day})" if self.time_of_day else ""
        return (
            f"[{self.priority.name}] {self.name} — {self.task_type}, "
            f"{self.duration} min{time_label} | {self.frequency} | {status}"
        )


@dataclass
class Pet:
    """Stores pet details and owns a list of care tasks."""
    name: str
    species: str
    breed: str
    age: int
    special_needs: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its unique id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Return all tasks matching a given priority level."""
        return [t for t in self.tasks if t.priority == priority]

    def get_profile(self) -> str:
        """Return a readable summary of the pet's profile."""
        needs = ", ".join(self.special_needs) if self.special_needs else "None"
        return (
            f"{self.name} | {self.species} ({self.breed}) | Age: {self.age} | "
            f"Special needs: {needs} | Tasks: {len(self.tasks)}"
        )


class Owner:
    """Manages one or more pets and provides access to all their tasks."""

    def __init__(self, name: str, available_time: int, preferences: List[str] = None):
        """Initialize an owner with name, available time, and optional preferences."""
        self.name = name
        self.available_time = available_time    # total minutes available per day
        self.preferences = preferences or []
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> List[Task]:
        """Collect and return every task across all owned pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def set_availability(self, time: int) -> None:
        """Update how many minutes per day the owner has available."""
        self.available_time = time

    def add_preference(self, preference: str) -> None:
        """Add a scheduling preference (e.g. 'morning walks', 'no tasks after 8pm')."""
        if preference not in self.preferences:
            self.preferences.append(preference)


class Scheduler:
    """Retrieves, organizes, and manages tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        """Initialize a scheduler for the given owner."""
        self.owner = owner
        self.scheduled_tasks: List[Task] = []
        self.reasoning: List[str] = []
        self.total_duration: int = 0

    def generate_plan(self) -> None:
        """Build a daily plan from all owner tasks, respecting time, frequency, and priority."""
        self.scheduled_tasks = []
        self.reasoning = []
        self.total_duration = 0

        all_tasks = self.owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.completed]
        freq_filtered = self._filter_by_frequency(incomplete)
        time_filtered = self._filter_by_time(freq_filtered)
        sorted_tasks = self._sort_by_priority_and_time(time_filtered)

        for task in sorted_tasks:
            if self._fits_within_available_time(self.scheduled_tasks + [task]):
                self.scheduled_tasks.append(task)
                self.total_duration += task.duration
                self.reasoning.append(
                    f"Added '{task.name}' ({task.priority.name}, {task.duration} min)"
                )
            else:
                self.reasoning.append(
                    f"Skipped '{task.name}' — would exceed available time of "
                    f"{self.owner.available_time} min"
                )

    def _filter_by_frequency(self, tasks: List[Task]) -> List[Task]:
        """Include daily tasks always; weekly tasks only on Mondays; skip as-needed tasks."""
        today = datetime.date.today().weekday()  # 0 = Monday
        result = []
        for t in tasks:
            if t.frequency == "daily":
                result.append(t)
            elif t.frequency == "weekly":
                if today == 0:
                    result.append(t)
                else:
                    self.reasoning.append(
                        f"Skipped '{t.name}' — weekly task, only scheduled on Mondays"
                    )
            # as-needed tasks are excluded unless manually added to the plan
        return result

    def _filter_by_time(self, tasks: List[Task]) -> List[Task]:
        """
        If the owner has time-of-day preferences, prioritise matching tasks first.
        Tasks with no time_of_day set are always included.
        """
        preferred_times = [p for p in self.owner.preferences if p in ("morning", "afternoon", "evening")]
        if not preferred_times:
            return tasks
        preferred = [t for t in tasks if t.time_of_day in preferred_times]
        others = [t for t in tasks if t.time_of_day not in preferred_times]
        return preferred + others

    @staticmethod
    def _to_minutes(time_str: str) -> int:
        """Convert 'HH:MM' string to total minutes since midnight."""
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by Priority enum value (HIGH=1 first)."""
        return sorted(tasks, key=lambda t: t.priority.value)

    def _sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by start_time (HH:MM). Tasks without a time are placed last."""
        return sorted(tasks, key=lambda t: self._to_minutes(t.start_time) if t.start_time else 9999)

    def _sort_by_priority_and_time(self, tasks: List[Task]) -> List[Task]:
        """Sort by priority first, then by start_time within the same priority level."""
        return sorted(tasks, key=lambda t: (
            t.priority.value,
            self._to_minutes(t.start_time) if t.start_time else 9999
        ))

    def _fits_within_available_time(self, tasks: List[Task]) -> bool:
        """Return True if the combined duration of tasks fits the owner's available time."""
        return sum(t.duration for t in tasks) <= self.owner.available_time

    def add_task(self, pet_name: str, task: Task) -> None:
        """Add a task directly to a named pet via the scheduler."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                pet.add_task(task)
                return
        raise ValueError(f"No pet named '{pet_name}' found.")

    def remove_task(self, task_id: str) -> None:
        """Remove a task by id from whichever pet owns it."""
        for pet in self.owner.pets:
            pet.remove_task(task_id)

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task complete and auto-create the next occurrence for daily/weekly tasks.

        Returns the new Task if one was created, or None for as-needed tasks.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.id == task_id:
                    task.mark_complete()
                    renewed = task.renew()
                    if renewed:
                        pet.add_task(renewed)
                    return renewed
        raise ValueError(f"No task with id '{task_id}' found.")

    def display(self) -> str:
        """Return a formatted string of the scheduled plan."""
        if not self.scheduled_tasks:
            return "No plan generated yet. Call generate_plan() first."
        lines = [f"Daily Plan for {self.owner.name} ({self.total_duration} min total)\n"]
        for i, task in enumerate(self.scheduled_tasks, 1):
            lines.append(f"  {i}. {task.get_summary()}")
        return "\n".join(lines)

    def get_reasoning(self) -> str:
        """Return the reasoning log from the last generate_plan() call."""
        if not self.reasoning:
            return "No reasoning available. Call generate_plan() first."
        return "\n".join(f"- {r}" for r in self.reasoning)

    def detect_conflicts(self) -> List[str]:
        """Flag time slot overloads, duplicate task types, and start_time window overlaps."""
        active = [t for t in self.owner.get_all_tasks() if not t.completed]
        return self._check_slot_conflicts(active) + self._check_overlap_conflicts(active)

    def _check_slot_conflicts(self, tasks: List[Task]) -> List[str]:
        """Flag slots where total duration exceeds budget or task types are duplicated."""
        conflicts = []
        slot_groups: dict = defaultdict(list)
        for task in tasks:
            if task.time_of_day:
                slot_groups[task.time_of_day].append(task)

        for slot, slot_tasks in slot_groups.items():
            total = sum(t.duration for t in slot_tasks)
            if total > TIME_SLOT_BUDGET.get(slot, 120):
                names = ", ".join(t.name for t in slot_tasks)
                conflicts.append(
                    f"Time overload in {slot}: {total} min [{names}] "
                    f"exceeds {TIME_SLOT_BUDGET[slot]} min budget"
                )
        return conflicts

    def _check_overlap_conflicts(self, tasks: List[Task]) -> List[str]:
        """Flag pairs of tasks whose start_time windows physically overlap."""
        conflicts = []
        timed = sorted(
            [t for t in tasks if t.start_time],
            key=lambda t: self._to_minutes(t.start_time)
        )
        for i, a in enumerate(timed):
            a_end = self._to_minutes(a.start_time) + a.duration
            for b in timed[i + 1:]:
                b_start = self._to_minutes(b.start_time)
                if b_start >= a_end:
                    break  # sorted, so no further overlaps possible
                conflicts.append(
                    f"Overlap: '{a.name}' ({a.start_time}, {a.duration} min) and "
                    f"'{b.name}' ({b.start_time}, {b.duration} min) "
                    f"overlap by {a_end - b_start} min"
                )
        return conflicts

    def filter_tasks(self, task_type: str = None, priority: Priority = None, pet_name: str = None) -> List[Task]:
        """Return tasks matching all provided filters (None = no filter on that field)."""
        if pet_name:
            tasks = []
            for pet in self.owner.pets:
                if pet.name == pet_name:
                    tasks = list(pet.tasks)
                    break
        else:
            tasks = self.owner.get_all_tasks()

        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]
        if priority is not None:
            tasks = [t for t in tasks if t.priority == priority]
        return tasks
