from dataclasses import dataclass
import platform
import resource
from time import perf_counter_ns, sleep
from typing import Callable, Iterable

MIB = 1024 * 1024
MAX_TOTAL_MIB = 512


@dataclass(frozen=True)
class Observation:
    step_bytes: int
    step_elapsed_ns: int
    allocated_bytes: int
    elapsed_ns: int
    baseline_peak_rss_bytes: int
    peak_rss_bytes: int
    peak_rss_step_delta_bytes: int
    peak_rss_delta_bytes: int


@dataclass(frozen=True)
class ProbeSummary:
    step_count: int
    allocated_bytes: int
    elapsed_ns: int
    baseline_peak_rss_bytes: int
    maximum_peak_rss_bytes: int
    peak_rss_delta_bytes: int
    largest_step_peak_rss_delta_bytes: int


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


def read_peak_rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return peak_rss_bytes(usage.ru_maxrss)


def run_probe(
    total_mib: int,
    step_mib: int,
    *,
    pause_seconds: float = 0,
    clock: Callable[[], int] = perf_counter_ns,
    rss_reader: Callable[[], int] = read_peak_rss_bytes,
) -> list[Observation]:
    if pause_seconds < 0:
        raise ValueError("pause_seconds must be non-negative")
    retained: list[bytearray] = []
    observations: list[Observation] = []
    allocated = 0
    baseline_peak_rss = rss_reader()
    previous_peak_rss = baseline_peak_rss
    started = clock()
    previous = started
    for size in allocation_plan(total_mib, step_mib):
        retained.append(bytearray(size))
        allocated += size
        if pause_seconds:
            sleep(pause_seconds)
        peak_rss = rss_reader()
        observed_at = clock()
        if observed_at < previous:
            raise ValueError("clock must be monotonic")
        observations.append(
            Observation(
                size,
                observed_at - previous,
                allocated,
                observed_at - started,
                baseline_peak_rss,
                peak_rss,
                max(0, peak_rss - previous_peak_rss),
                max(0, peak_rss - baseline_peak_rss),
            )
        )
        previous = observed_at
        previous_peak_rss = max(previous_peak_rss, peak_rss)
    return observations


def summarize_observations(observations: Iterable[Observation]) -> ProbeSummary:
    items = list(observations)
    if not items:
        raise ValueError("at least one observation is required")
    baseline = items[0].baseline_peak_rss_bytes
    if any(item.baseline_peak_rss_bytes != baseline for item in items):
        raise ValueError("observations must share one baseline")
    if any(
        current.allocated_bytes < previous.allocated_bytes
        or current.elapsed_ns < previous.elapsed_ns
        for previous, current in zip(items, items[1:])
    ):
        raise ValueError("observations must be in cumulative order")
    return ProbeSummary(
        step_count=len(items),
        allocated_bytes=items[-1].allocated_bytes,
        elapsed_ns=items[-1].elapsed_ns,
        baseline_peak_rss_bytes=baseline,
        maximum_peak_rss_bytes=max(item.peak_rss_bytes for item in items),
        peak_rss_delta_bytes=max(item.peak_rss_delta_bytes for item in items),
        largest_step_peak_rss_delta_bytes=max(
            item.peak_rss_step_delta_bytes for item in items
        ),
    )
