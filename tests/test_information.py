"""Integration checks against the user's JIDT jar; no Python JVM bridge required."""
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from information_analysis import exclusion_audit, match_lag, ROOT, RUNS

JAR=Path('/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar')


class AlignmentTests(unittest.TestCase):
    def test_half_hour_lag_matches_real_timestamps(self):
        data=match_lag('stockton',.5)
        diff=data.near_timestamp_utc-data.timestamp_utc
        self.assertTrue(diff.eq(pd.Timedelta(minutes=30)).all())
        self.assertTrue(data.timestamp_utc.dt.minute.eq(0).all())
        self.assertTrue(data.near_timestamp_utc.dt.minute.eq(30).all())

    def test_conservative_exclusion_never_misses_short_elapsed_pairs(self):
        t=pd.Timestamp('2020-01-01',tz='UTC')+pd.to_timedelta([0,1,2,10,11,12],unit='h')
        d=exclusion_audit(pd.DataFrame({'timestamp_utc':t}),4)
        self.assertEqual(d['physical_pairs_within_window'],6)
        self.assertEqual(d['row_index_excluded_pairs'],14)
        self.assertEqual(d['extra_pairs_excluded_across_gaps'],8)


@unittest.skipUnless(JAR.exists(),'JIDT integration jar unavailable')
class JavaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['javac','-cp',str(JAR),'-d',str(RUNS),str(ROOT/'src/java/WaveInformation.java')],check=True,capture_output=True)

    def calculate(self,raw,measure):
        values=(raw-raw.mean(axis=0))/raw.std(axis=0,ddof=1)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data.csv'; output=Path(tmp)/'results.csv'
            np.savetxt(path,values,delimiter=',')
            command=['java','-cp',str(RUNS)+':'+str(JAR),'WaveInformation',str(path),str(output),measure,'4','0','9','0','123']
            subprocess.run(command,check=True,capture_output=True)
            a=pd.read_csv(output)
            subprocess.run(command,check=True,capture_output=True)
            b=pd.read_csv(output)
            pd.testing.assert_frame_equal(a,b)
            self.assertAlmostEqual(a.iloc[0].bits,a.iloc[0].nats/np.log(2))
            self.assertEqual(len(a),10)
            return a.iloc[0].bits

    def test_gaussian_mi_and_conditional_confounding(self):
        rng=np.random.default_rng(173); n=4000
        z=rng.normal(size=n); x=z+rng.normal(size=n); y=z+rng.normal(size=n)
        raw=np.column_stack([z,y,x,rng.normal(size=n),rng.normal(size=n)])
        mi=self.calculate(raw,'mi_height')
        # z and y=z+noise: population MI = 0.5 bit.
        self.assertAlmostEqual(mi,.5,delta=.1)
        cmi=self.calculate(raw,'cmi_period')
        self.assertLess(abs(cmi),.1)  # X and Y share Z, but independent conditional on Z
        raw[:,1]=x+z+rng.normal(size=n)
        self.assertGreater(self.calculate(raw,'cmi_period'),.3)


if __name__=='__main__': unittest.main()
