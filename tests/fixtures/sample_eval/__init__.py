"""A minimal eval used by the README generator tests."""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import exact
from inspect_ai.solver import generate


@task
def sample_task(limit: int = 5, shuffle: bool = False) -> Task:
    """A sample task.

    Args:
        limit: How many samples to take.
        shuffle: Whether to shuffle the dataset.
    """
    samples = [Sample(input=f"q{i}", target=f"a{i}") for i in range(limit)]
    return Task(dataset=samples, solver=generate(), scorer=exact())
