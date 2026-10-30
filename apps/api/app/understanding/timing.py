"""Optional monotonic phase measurements; never change validation or persistence."""
from contextlib import contextmanager
from time import perf_counter


@contextmanager
def measured_phase(measure, name):
    started=perf_counter()
    try:
        yield
    finally:
        if measure:
            measure(**{name:(perf_counter()-started)*1000})
