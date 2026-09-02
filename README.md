# memory-pressure-lab

A bounded, explicit memory-pressure probe for observing how a process behaves
as resident memory grows. The default command is a dry run; allocation starts
only when `--run` is supplied.

```bash
PYTHONPATH=src python3 -m memory_pressure_lab --total-mib 64 --step-mib 8
PYTHONPATH=src python3 -m memory_pressure_lab --total-mib 64 --step-mib 8 --run
python3 -m unittest discover -s tests
```

The probe caps requested allocation at 512 MiB and reports observed peak RSS.
Peak RSS is a process high-water mark, not current live memory, and operating
systems may account for resident pages differently.

