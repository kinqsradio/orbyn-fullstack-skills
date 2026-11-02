"""A small task list."""


def add_task(tasks, title):
    return tasks + [{'title': title, 'done': False}]


def complete(tasks, title):
    return [dict(t, done=True) if t['title'] == title else t for t in tasks]


def summary(tasks):
    """Return {'open': n, 'done': n, 'ratio': done / total rounded to 2 places, 0.0 with no tasks}."""
    raise NotImplementedError  # TODO
