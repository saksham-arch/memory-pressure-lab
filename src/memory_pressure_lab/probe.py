from dataclasses import dataclass
import platform
import resource
from time import perf_counter_ns, sleep
from typing import Callable

MIB = 1024 * 1024
MAX_TOTAL_MIB = 512


@dataclass(frozen=True)
class Observation:
    step_bytes: int
    step_elapsed_ns: int
    allocated_bytes: int
    elapsed_ns: int
    peak_rss_bytes: int


def allocation_plan(total_mib: int, step_mib: int) -> list[int]:
    if total_mib < 1 or total_mib > MAX_TOTAL_MIB:
        raise ValueError(f"total_mib must be between 1 and {MAX_TOTAL_MIB}")
    if step_mib < 1 or step_mib > total_mib:
        raise ValueError("step_mib must be between 1 and total_mib")
    plan: list[int] = []
    remaining = total_mib
    while remaining:
        next_step = min(step_mib, remaining)
        plan.append(next_step * MIB)
        remaining -= next_step
    return plan


def peak_rss_bytes(raw_value: int, system: str = platform.system()) -> int:
    """Normalize getrusage peak RSS, which is KiB on Linux and bytes on macOS."""
    return raw_value * 1024 if system == "Linux" else raw_value


def run_probe(
    total_mib: int,
    step_mib: int,
    *,
    pause_seconds: float = 0,
    clock: Callable[[], int] = perf_counter_ns,
) -> list[Observation]:
    if pause_seconds < 0:
        raise ValueError("pause_seconds must be non-negative")
    retained: list[bytearray] = []
    observations: list[Observation] = []
    allocated = 0
    started = clock()
    previous = started
    for size in allocation_plan(total_mib, step_mib):
        retained.append(bytearray(size))
        allocated += size
        if pause_seconds:
            sleep(pause_seconds)
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        observed_at = clock()
        if observed_at < previous:
            raise ValueError("clock must be monotonic")
        observations.append(
            Observation(
                size,
                observed_at - previous,
                allocated,
                observed_at - started,
                peak_rss_bytes(rss),
            )
        )
        previous = observed_at
    return observations
