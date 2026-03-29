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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
