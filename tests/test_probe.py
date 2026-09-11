import unittest

from memory_pressure_lab.probe import MIB, allocation_plan, peak_rss_bytes, run_probe


class ProbeTests(unittest.TestCase):
    def test_plan_includes_partial_final_step(self) -> None:
        self.assertEqual(allocation_plan(10, 4), [4 * MIB, 4 * MIB, 2 * MIB])

    def test_rejects_unsafe_or_invalid_plans(self) -> None:
        for total, step in ((0, 1), (513, 1), (8, 0), (8, 9)):
            with self.subTest(total=total, step=step), self.assertRaises(ValueError):
                allocation_plan(total, step)

    def test_normalizes_linux_peak_rss(self) -> None:
        self.assertEqual(peak_rss_bytes(2, "Linux"), 2048)
        self.assertEqual(peak_rss_bytes(2, "Darwin"), 2)

    def test_small_probe_reports_each_step(self) -> None:
        ticks = iter([0, 10, 20])
        rss_values = iter([100, 120, 150])
        results = run_probe(
            2,
            1,
            clock=lambda: next(ticks),
            rss_reader=lambda: next(rss_values),
        )
        self.assertEqual([item.step_bytes for item in results], [MIB, MIB])
        self.assertEqual([item.step_elapsed_ns for item in results], [10, 10])
        self.assertEqual([item.allocated_bytes for item in results], [MIB, 2 * MIB])
        self.assertEqual([item.elapsed_ns for item in results], [10, 20])
        self.assertEqual([item.peak_rss_delta_bytes for item in results], [20, 50])

    def test_rejects_non_monotonic_clock(self) -> None:
        ticks = iter([10, 5])
        with self.assertRaises(ValueError):
            run_probe(1, 1, clock=lambda: next(ticks), rss_reader=lambda: 100)

    def test_peak_rss_delta_never_goes_negative(self) -> None:
        rss_values = iter([100, 90])
        result = run_probe(
            1,
            1,
            clock=iter([0, 1]).__next__,
            rss_reader=lambda: next(rss_values),
        )
        self.assertEqual(result[0].peak_rss_delta_bytes, 0)


if __name__ == "__main__":
    unittest.main()
