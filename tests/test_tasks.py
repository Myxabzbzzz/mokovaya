from services.tasks import EASY_TASKS, MEDIUM_TASKS, pick_random_task


class _FakeRandom:
    def __init__(self, random_value, choice_index=0):
        self._random_value = random_value
        self._choice_index = choice_index

    def random(self):
        return self._random_value

    def choice(self, seq):
        return seq[self._choice_index]


def test_pick_random_task_picks_easy_below_threshold():
    rng = _FakeRandom(random_value=0.5, choice_index=2)

    task = pick_random_task(rng)

    assert task == EASY_TASKS[2]


def test_pick_random_task_picks_medium_at_or_above_threshold():
    rng = _FakeRandom(random_value=0.9, choice_index=1)

    task = pick_random_task(rng)

    assert task == MEDIUM_TASKS[1]


def test_easy_and_medium_pools_are_non_empty():
    assert len(EASY_TASKS) > 0
    assert len(MEDIUM_TASKS) > 0


def test_all_tasks_have_matching_difficulty_field():
    assert all(t.difficulty == "easy" for t in EASY_TASKS)
    assert all(t.difficulty == "medium" for t in MEDIUM_TASKS)


def test_all_tasks_have_title_source_and_url():
    for task in EASY_TASKS + MEDIUM_TASKS:
        assert task.title
        assert task.source
        assert task.url.startswith("https://")
