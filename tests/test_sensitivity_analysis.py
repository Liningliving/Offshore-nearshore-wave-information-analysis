import sys
import unittest
from pathlib import Path
import tempfile
import subprocess
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sensitivity_analysis import match_frames,load_lags,ROOT


class ExactLagMatchingTests(unittest.TestCase):
    def test_half_hour_targets_and_gaps_are_not_row_shifts(self):
        start=pd.Timestamp('2020-01-01',tz='UTC')
        off=pd.DataFrame({'timestamp_utc':start+pd.to_timedelta([0,1,3],unit='h'),'Ho':[1.,2.,3.],'Tp_o':[8.,9.,10.],'Dx':[1.,1.,1.],'Dy':[0.,0.,0.]})
        near=pd.DataFrame({'near_timestamp_utc':start+pd.to_timedelta([0,.5,1,1.5,3.5],unit='h'),'Hn':[10.,15.,20.,25.,45.]})
        matched=match_frames(off,near,.5)
        np.testing.assert_array_equal(matched.Hn,[15.,25.,45.])
        np.testing.assert_array_equal(matched.Ho,[1.,2.,3.])
        self.assertEqual(len(match_frames(off,near,0)),2)

    def test_rematched_zero_lag_equals_both_original_cleaned_files(self):
        for site in ['figure_eight_pools','stockton']:
            frames=load_lags(site);original=pd.read_csv(ROOT/f'data/processed/{site}.csv')
            np.testing.assert_allclose(frames[0][['Ho','Hn','Tp_o','Dx','Dy']],original[['Ho','Hn','Tp_o','Dx','Dy']],rtol=0,atol=1e-14)
            self.assertTrue(frames[.5].near_timestamp_utc.dt.minute.eq(30).all())
            common=set.intersection(*(set(f.timestamp_utc) for f in frames.values()))
            for frame in frames.values():self.assertEqual(frame.timestamp_utc.isin(common).sum(),len(common))


@unittest.skipUnless((ROOT/'tools/jidt/build/infodynamics.jar').exists(),'Official build unavailable; no Java proof')
class SensitivityJavaIntegrationTests(unittest.TestCase):
    def test_actual_hourly_and_half_hourly_masks_all_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar=ROOT/'tools/jidt/build/infodynamics.jar'
            files=['ElapsedHourLoader.java','SharedEstimatorSettings.java','SensitivitySettings.java','SensitivityIntegrationCheck.java']
            subprocess.run(['javac','-cp',str(jar),'-d',tmp,*[str(ROOT/'src/java'/p) for p in files]],check=True,capture_output=True)
            output=Path(tmp)/'evidence.csv'
            subprocess.run(['java','-cp',tmp+':'+str(jar),'SensitivityIntegrationCheck',str(output)],check=True,capture_output=True)
            d=pd.read_csv(output)
            self.assertEqual(len(d),12)
            self.assertTrue(d[['mi_pass','period_cmi_pass','direction_cmi_pass','boundary_and_gap_masks_pass']].all().all())
            np.testing.assert_allclose(d.window_hours,d.window_ticks*d.index_unit_hours)
            self.assertEqual(set(d.k),{3,4,6,8})
            self.assertEqual(set(d.window_hours),{30,45,60})


if __name__=='__main__':unittest.main()
