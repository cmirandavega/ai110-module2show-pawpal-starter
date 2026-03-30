# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The scheduling logic in `pawpal_system.py` has been upgraded with several algorithms that make the daily plan more intelligent and realistic.

**Priority + time sorting**
Tasks are sorted by priority first (HIGH → MEDIUM → LOW), then by `start_time` within the same priority level. A `start_time` field in `HH:MM` format was added to `Task` so the scheduler can order tasks chronologically across the day rather than by insertion order.

**Frequency filtering**
Tasks have a `frequency` field (`daily`, `weekly`, `as-needed`). The scheduler now acts on it — daily tasks are always included, weekly tasks are only scheduled on Mondays, and as-needed tasks are excluded unless manually added. Skipped tasks are logged in the scheduling reasoning.

**Conflict detection**
Before or after generating a plan, `detect_conflicts()` checks for three types of problems:
- Time slot overload — tasks in the same slot (morning/afternoon/evening) exceed the 120-minute slot budget
- Duplicate task types — two tasks of the same type (e.g. two `feeding` tasks) in the same slot
- Window overlap — two tasks whose `start_time` + `duration` windows physically overlap, with the exact overlap in minutes reported

**Recurring task renewal**
When a task is marked complete via `complete_task()`, the scheduler automatically creates a fresh copy for the next occurrence — tomorrow for daily tasks, one week later for weekly tasks. The new task gets a `next_due` date and a unique ID, leaving the completed original intact in the task history.

**Task filtering**
`filter_tasks()` lets you query the full task list by any combination of `task_type`, `priority`, or `pet_name` without generating a full plan.

---

## Testing PawPal+

### Running the tests

```bash
python -m pytest
```

To see detailed output for each test:

```bash
python -m pytest -v
```

### What the tests cover

The test suite in `tests/test_pawpal.py` contains 22 tests across four areas:

| Area | What is verified |
|---|---|
| **Sorting correctness** | Tasks are returned in chronological order; HIGH priority always comes before LOW; tasks with no `start_time` are placed last; time is used as a tiebreaker within the same priority level |
| **Recurrence logic** | Completing a daily task creates a new task due tomorrow; weekly tasks renew 7 days out; `as-needed` tasks produce no renewal; all original fields (name, duration, priority) are preserved on the renewed task |
| **Conflict detection** | Overlapping time windows are flagged with the exact overlap in minutes; touching tasks (no gap, no overlap) are not falsely flagged; slot overloads above 120 min are caught; duplicate task types in the same slot are reported; the exact-120-min boundary does not trigger a false overload |
| **Time budget** | Tasks that would exceed `available_time` are skipped and logged; a zero-minute budget produces an empty plan; tasks whose combined duration exactly equals the budget are all included |

### Confidence Level

★★★★☆ (4 / 5)

All 22 tests pass and cover the core scheduling behaviors, edge cases, and boundary conditions. One star is withheld because the test suite does not yet cover the Streamlit UI layer or multi-pet scheduling interactions, so end-to-end behavior in the app remains manually verified only.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
