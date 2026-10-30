"""Run with python3 -m unittest discover -s tests."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from autocorrelation import VARIABLES, lagged_acf, decay_summary, THRESHOLD
from jidt_timing import timed_blocks, load_observations


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.hours = np.array([0, 1, 2, 10, 11, 12])
        self.times = pd.Timestamp('2020-01-01', tz='UTC') + pd.to_timedelta(self.hours, unit='h')

    def test_acf_pairs_follow_elapsed_time(self):
        x = np.array([0., 1., 4., 3., 2., 8.])
        data = pd.DataFrame({'timestamp_utc': self.times, **{v: x for v in VARIABLES}})
        acf = lagged_acf(data, 10).query("variable == 'Ho'").set_index('lag_hours')
        self.assertEqual(acf.loc[1, 'observed_pairs'], 4)  # not five compressed neighbours
        self.assertEqual(acf.loc[3, 'observed_pairs'], 0)
        self.assertEqual(acf.loc[10, 'observed_pairs'], 3)
        self.assertAlmostEqual(acf.loc[1, 'acf'], np.corrcoef(x[[0,1,3,4]], x[[1,2,4,5]])[0,1])
        self.assertAlmostEqual(acf.loc[0, 'acf'], 1)

    def test_window_requires_sustained_decay(self):
        acf = pd.DataFrame({'variable': 'Ho', 'lag_hours': range(10),
                            'acf': [1,.2,.8,.2,.2,.2,.2,.2,.2,.2], 'observed_pairs': 1000})
        row = decay_summary(acf, 'test')[0]
        self.assertEqual(row['first_abs_acf_below_1e_hours'], 1)
        self.assertEqual(row['sustained_abs_acf_below_1e_hours'], 3)
        acf['acf'] = 1
        self.assertIsNone(decay_summary(acf, 'test')[0]['sustained_abs_acf_below_1e_hours'])

    def test_off_grid_is_not_silently_rounded(self):
        with self.assertRaises(ValueError):
            list(timed_blocks(self.times + pd.Timedelta(minutes=30)))

    def test_jidt_loading_preserves_gap_and_shared_trial(self):
        class Recorder:
            def __init__(self): self.calls=[]; self.properties={}
            def setProperty(self, k, v): self.properties[k]=v
            def startAddObservations(self): pass
            def finaliseAddObservations(self): pass
            def addObservationsTrackObservationIDs(self, *args): self.calls.append(args)
        for dimensions in [(1,1), (2,1,1)]:
            calc=Recorder()
            arrays=[np.ones((6,d)) for d in dimensions]
            load_observations(calc, self.times, arrays, 4, lambda a:a)
            self.assertEqual([c[-2:] for c in calc.calls], [(0,0),(0,10)])
            self.assertEqual([len(c[0]) for c in calc.calls], [3,3])
            self.assertEqual(calc.properties['DYN_CORR_EXCL'], '4')
            # With actual indices, the last pre-gap and first post-gap points are
            # eight hours apart, whereas compressed row indices differ by one.
            self.assertGreater(self.hours[3]-self.hours[2], 4)
            self.assertLessEqual(3-2, 4)


if __name__ == '__main__':
    unittest.main()
