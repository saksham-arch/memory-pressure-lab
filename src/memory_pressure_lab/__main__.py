import argparse
from dataclasses import asdict
import json

from .probe import allocation_plan, run_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded memory-pressure probe")
    parser.add_argument("--total-mib", type=int, required=True)
    parser.add_argument("--step-mib", type=int, required=True)
    parser.add_argument("--pause-seconds", type=float, default=0)
    parser.add_argument("--run", action="store_true", help="perform allocations; default is dry-run")
    args = parser.parse_args()
    if args.run:
        payload = [asdict(item) for item in run_probe(args.total_mib, args.step_mib, pause_seconds=args.pause_seconds)]
    else:
        payload = {"dry_run": True, "allocation_steps_bytes": allocation_plan(args.total_mib, args.step_mib)}
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

