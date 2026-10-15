# memory-pressure-lab

A bounded, explicit memory-pressure probe for observing how a process behaves
as resident memory grows. The default command is a dry run; allocation starts
only when `--run` is supplied.

```bash
PYTHONPATH=src python3 -m memory_pressure_lab --total-mib 64 --step-mib 8
PYTHONPATH=src python3 -m memory_pressure_lab --total-mib 64 --step-mib 8 --run
PYTHONPATH=src python3 -m memory_pressure_lab --total-mib 64 --step-mib 8 --run --summary
python3 -m unittest discover -s tests
```

The probe caps requested allocation at 512 MiB and reports per-step elapsed time
(including any requested pause), cumulative elapsed time, and observed peak
RSS. Peak RSS is a process high-water mark, not current live memory, and
operating systems may account for resident pages differently.

Each observation also reports peak-RSS growth relative to the process baseline
captured immediately before the probe. Since peak RSS is monotonic on supported
platforms, that delta describes high-water growth rather than retained live
memory. The baseline value is retained in every observation, and per-step
growth reports only a new increase beyond the greatest peak seen by earlier
steps. A zero step delta means the recorded high-water mark did not advance; it
does not prove that the allocation had no memory cost.

`--summary` retains every observation and adds step count, requested allocation,
elapsed time, median and maximum step elapsed time, the largest per-step peak
increase, and total peak-RSS growth from the shared baseline. Step timing covers
the entire probe step, including any requested pause, RSS sampling, and clock
overhead; it is useful for spotting outlier steps but is not allocator-only
latency. The summary also reports `peak_rss_growth_ratio`, which divides growth
by requested allocation. The ratio can be below or above 1 because of allocator
behavior, page accounting, unrelated process activity, and an already-elevated
high-water mark. It is an observation for comparing controlled runs, not an
allocation-efficiency score. These remain high-water-mark observations; the
summary does not estimate current live memory or prove that memory is retained.
