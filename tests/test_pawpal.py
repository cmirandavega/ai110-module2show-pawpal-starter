from pawpal_system import Task, Pet, Priority


def test_mark_complete_changes_status():
    """Calling mark_complete() should set the task's completed flag to True."""
    task = Task(
        name="Morning Walk",
        task_type="walk",
        duration=30,
        priority=Priority.HIGH
    )
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list length by one."""
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    assert len(pet.tasks) == 0

    task = Task(
        name="Breakfast Feeding",
        task_type="feeding",
        duration=10,
        priority=Priority.HIGH
    )
    pet.add_task(task)
    assert len(pet.tasks) == 1
