# PawPal+ Project Reflection

## 1. System Design
- Enter owner + pet info — set up a basic profile with details about the owner and their pet

- Add/edit tasks — create and manage care tasks (walks, feeding, meds, grooming, etc.) with duration and priority

- Generate and view a daily plan — produce a schedule based on constraints/priorities and see it displayed with reasoning
**a. Initial design**

- Briefly describe your initial UML design.
   Owner — holds the pet owner's name, available time, and preferences. Controls availability and preference settings.

  Pet — holds the pet's profile info (name, species, breed, age, special needs). Can return a summary of that profile.

  Task — represents a single care activity with a type, duration, priority, and optional time-of-day preference. Can be edited and summarized.

  Scheduler — the central class that connects everything. It holds references to the Owner and Pet, manages the task list, and generates the daily plan. It also stores the output — the ordered schedule, total duration, and reasoning. 
- What classes did you include, and what responsibilities did you assign to each?
    Owner — responsible for storing who the user is and their constraints. It knows how much time is available and what preferences the owner has for scheduling.

    Pet — responsible for holding all profile data about the pet. It answers the question "who is being cared for?" and surfaces any special needs that might affect scheduling.

    Task — responsible for representing a single care activity. It owns its own data (type, duration, priority) and can describe itself or be updated.

    Scheduler — responsible for the core logic of the app. It takes the owner's constraints, the pet's needs, and the full task list, then produces an ordered daily plan with reasoning. It is the bridge between data and output.

**b. Design changes**

- Did your design change during implementation?
  Yes. After reviewing the initial design for missing relationships and logic bottlenecks, several issues were identified that required changes.

- If yes, describe at least one change and why you made it.
  The initial design had no link between Owner and Pet — the UML defined that relationship but the Owner class held no pet attribute. This was corrected by adding pet as a parameter and attribute on Owner so the relationship exists in code, not just in the diagram.

**Documented changes made to pawpal_system.py:**

1. **Added `Priority` enum** — replaced raw strings (`"high"`, `"medium"`, `"low"`) on `Task`. Raw strings are unconstrained and a typo would not raise an error. An Enum makes valid values explicit and safe to sort on.

2. **Added unique `id` to `Task`** — `remove_task()` had no reliable way to identify a task. Two tasks with identical fields would be indistinguishable by value. A `uuid` field makes each task uniquely identifiable.

3. **Added `pet` attribute to `Owner`** — the UML defined `Owner --> Pet` but `Owner` held no reference to `Pet`. The relationship only existed inside `Scheduler`, which was inconsistent with the design.

4. **Changed `remove_task()` to accept `task_id: str`** — follows from the `id` addition above. Removal by object reference is unreliable for dataclasses; removal by unique id is unambiguous.

5. **Split `generate_plan()` into helper stubs** — all constraint checking, filtering, and sorting in one method would become a bottleneck. Added `_filter_by_time()`, `_sort_by_priority()`, and `_fits_within_available_time()` to keep each piece focused and independently testable.

6. **Added `_fits_within_available_time()` check** — `available_time` on `Owner` and `total_duration` on `Scheduler` were never connected. Without this check, tasks could silently overflow the owner's available day.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

  The scheduler considers three main constraints:

  1. **Available time** — the owner sets how many minutes they have in the day. The scheduler stops adding tasks the moment the total duration would exceed that budget.
  2. **Priority** — every task is tagged HIGH, MEDIUM, or LOW. The scheduler always attempts HIGH priority tasks first, so critical care (meds, feeding) is never pushed out by optional activities.
  3. **Start time** — tasks with an assigned start time are sorted chronologically within their priority group, so the plan reflects a realistic flow through the day rather than an arbitrary insertion order.

- How did you decide which constraints mattered most?

  The most important constraint is available time combined with priority. A schedule that ignores the owner's time limit is useless, and a schedule that doesn't protect high-priority tasks defeats the purpose of the app. Start time was added as a secondary constraint because sorting by priority alone would group tasks correctly but leave them in a random order within the day.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: Greedy scheduling over optimal packing**

The scheduler uses a greedy algorithm — it sorts tasks by priority and start_time, then adds each one in order as long as it fits within the owner's available time. Once a task is skipped because it would exceed the time budget, it stays skipped even if a shorter task later in the list could have filled that gap.

For example: if the owner has 20 minutes left and the next task needs 30 minutes, it is skipped. A 15-minute task that appears later in the sorted list would fit, but the scheduler does not backtrack to try it.

A more optimal approach — such as a knapsack algorithm — would evaluate all possible combinations and find the best-fitting set of tasks for the available time. However, that approach grows exponentially with the number of tasks and is significantly harder to reason about or debug.

The greedy approach is a reasonable tradeoff for this scenario because:
1. Pet care tasks are priority-ordered for a reason — a skipped HIGH priority task should be visible, not silently swapped out for a LOW priority one that happens to fit.
2. The task counts in a typical day are small (5–15 tasks), so the greedy approach rarely wastes meaningful time.
3. Simplicity matters — the scheduling reasoning log produced by the greedy approach is easy to read and explain to a non-technical user.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

  AI was used throughout the project for multiple purposes. During design it helped think through class responsibilities and catch missing relationships (like the Owner → Pet link that existed in the UML but not in the code). During implementation it helped write the scheduling logic, conflict detection, and the Streamlit UI. During testing it helped generate the test plan and write the pytest suite. It was also used for debugging when features like the schedule disappearing after marking a task complete needed a fix.

- What kinds of prompts or questions were most helpful?

  The most useful prompts were specific and gave context — for example asking "before going through with this code, would we need to change anything in pawpal_system.py to accommodate these changes?" rather than just asking for the code change directly. Asking the AI to explain what it was about to do and how it would affect everything else helped catch potential side effects before they became bugs.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

  When the AI suggested removing the duplicate task type conflict check entirely from `_check_slot_conflicts`, it was first questioned because that check existed for a reason. Rather than accepting the removal immediately, the reasoning was discussed — the AI explained that the overlap detection in `_check_overlap_conflicts` already handles the real timing conflict, and that flagging same-type tasks is too strict for pet care (a dog genuinely needs two walks per day). Only after that explanation made sense was the change accepted.

- How did you evaluate or verify what the AI suggested?

  Suggestions were verified in two ways: by asking the AI to explain each change and how it would affect the rest of the system before approving it, and by constantly testing each change in the running app to catch anything the AI missed. Several issues — like the schedule disappearing on rerun, the time display not updating after marking complete, and the duplicate walk conflict — were caught through hands-on testing rather than the AI flagging them proactively.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

  The test suite covers four core areas across 22 tests:

  1. **Sorting correctness** — verified that tasks come out in priority order (HIGH before LOW), that start time is used as a tiebreaker within the same priority, and that tasks with no start time are always placed last.
  2. **Recurrence logic** — verified that completing a daily task creates a new task due tomorrow, a weekly task renews 7 days out, an as-needed task produces no renewal, and that all original fields (name, duration, priority) carry over to the renewed task.
  3. **Conflict detection** — verified that overlapping time windows are flagged with the exact overlap in minutes, that touching tasks (one ends exactly when the next starts) are not falsely flagged, and that slot overloads above 120 minutes are caught while exactly 120 minutes is not.
  4. **Time budget** — verified that tasks exceeding the owner's available time are skipped, that a zero-minute budget produces an empty plan, and that tasks whose combined duration exactly equals the budget are all included.

- Why were these tests important?

  These behaviors are the core of what makes PawPal+ useful. If sorting is wrong, the daily plan is misleading. If recurrence breaks, the owner loses track of recurring care. If conflict detection has false positives or false negatives, either valid tasks get blocked or real problems go unreported. If the time budget isn't enforced correctly, the schedule becomes impossible to follow. Testing these ensured the logic was trustworthy before connecting it to the UI.

**b. Confidence**

- How confident are you that your scheduler works correctly?

  ★★★★☆ (4 / 5) — All 22 tests pass and cover the most important behaviors, boundary conditions, and edge cases in the backend logic. The confidence gap comes from the UI layer and multi-pet scheduling not being covered by automated tests. Those flows were verified manually through testing the running app, but manual testing is less reliable than automated tests.

- What edge cases would you test next if you had more time?

  - Multi-pet scheduling — verifying that tasks across two pets are sorted and conflict-checked correctly together
  - Tasks added after a plan is already generated — confirming the plan regenerates cleanly without stale data
  - Weekly tasks on days other than Monday — ensuring they are consistently excluded and logged
  - Marking all tasks complete in one session — verifying the renewal chain works correctly back-to-back
  - Very large task lists — checking that performance and sort order hold up with 20+ tasks

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

  The conflict prevention system is the part that came together best. Rather than just flagging conflicts after the fact, the app blocks a task from being added the moment it would create a problem and explains exactly why. It does this by running a tentative-add check — adding the task, detecting whether any new conflicts appeared, and rolling it back if they did. That combination of proactive blocking and clear feedback makes the app feel genuinely useful rather than just a list manager.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

  The biggest improvement would be an edit task feature. Right now if a task was added with the wrong time or duration the only option is to remove and re-add it. Adding an inline edit directly in the task table would make the app much more practical. A second improvement would be multi-pet support in the UI — the backend already supports multiple pets through the Owner class, but the app only exposes one pet at a time. Exposing that would make PawPal+ genuinely useful for households with more than one animal.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

  The most important thing learned was that AI is most useful when you treat it as a collaborator to question, not an authority to follow. Every time a suggestion was asked to be explained before being accepted — and every time the running app was tested after a change — something was caught that the AI either missed or didn't flag. The habit of asking "how will this affect everything else?" before approving a change saved several bugs from making it into the final app. AI speeds up the work significantly, but the judgment about whether something is actually correct still has to come from the person using it.
