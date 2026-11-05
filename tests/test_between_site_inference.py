import sys
import unittest
from pathlib import Path
from decimal import Decimal
import csv
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from artifact_paths import resolve_artifact_path
from between_site_pilot import gaussian_truth,contrast,candidate_root_interval
ROOT=Path(__file__).resolve().parents[1]


class BetweenSiteTests(unittest.TestCase):
    def test_analytic_gaussian_information_truth_and_signs(self):
        # With only Ho -> Hn coupling at coefficient 1, I=0.5 ln 2.
        a=gaussian_truth((1,0,0))
        np.testing.assert_allclose(a,[.5*np.log(2),0,0])
        np.testing.assert_array_equal(contrast(a,a),[0,0,0])
        np.testing.assert_array_equal(contrast([3,1,2],[1,4,6]),[2,3,4])

    def test_unequal_site_root_scaling_is_not_raw_subsampling_quantiles(self):
        full_a=np.array([1.,2.,3.]);full_b=np.array([.1,.2,.3])
        ba=np.array([[1.2,2.2,3.2],[.8,1.8,2.8]])
        bb=np.array([[.3,.4,.5],[-.1,0.,.1]])
        observed,lo,hi,errors=candidate_root_interval(full_a,full_b,ba,bb,1000,2000,[250,250],[200,200])
        expected=contrast(.5*(ba-full_a),np.sqrt(.1)*(bb-full_b))
        np.testing.assert_allclose(errors,expected)
        np.testing.assert_allclose(lo,observed-np.quantile(expected,.975,axis=0))
        np.testing.assert_allclose(hi,observed-np.quantile(expected,.025,axis=0))

    def test_observed_contrasts_use_full_precision_and_have_no_fake_intervals(self):
        with (ROOT/'results/primary_information/primary_information_summary.csv').open() as f:source=list(csv.DictReader(f))
        new=pd.read_csv(ROOT/'results/primary_information/between_site_contrasts.csv',dtype=str)
        for row in new.itertuples():
            a=next(r for r in source if r['site']=='figure_eight_pools' and r['measure']==row.measure)
            b=next(r for r in source if r['site']=='stockton' and r['measure']==row.measure)
            sign=1 if row.contrast=='delta_height' else -1
            self.assertEqual(Decimal(row.observed_delta_bits),sign*(Decimal(a['bits'])-Decimal(b['bits'])))
        self.assertTrue(new[['lower_bits','upper_bits','p_two_sided']].isna().all().all())

    def test_blocks_contain_unique_joint_rows_and_preserve_elapsed_gaps(self):
        design=pd.read_csv(ROOT/'research/between_site_subsampling/validation/synthetic_design.csv')
        row=design.iloc[0]
        base=resolve_artifact_path(row.output_file)
        prefix=str(base).replace('_estimates.csv','')
        a=pd.read_csv(prefix+'_A.csv',header=None)
        b=pd.read_csv(prefix+'_B.csv',header=None)
        windows=pd.read_csv(prefix+'_blocks.csv',header=None)
        self.assertNotEqual(len(a),len(b))
        for site,data in enumerate([a,b]):
            self.assertTrue(data[0].is_unique)
            self.assertTrue((data[0].diff().dropna()>1).any())
            start,stop=windows.iloc[0,site*2:site*2+2]
            block=data.loc[data[0].ge(start)&data[0].lt(stop)]
            self.assertTrue(block[0].is_unique)
            self.assertEqual(block.shape[1],6)
            np.testing.assert_allclose(block[4]**2+block[5]**2,1)


if __name__=='__main__':unittest.main()
