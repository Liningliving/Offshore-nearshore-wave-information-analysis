import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from surrogate_methods import height_neighbours,local_order,compatible_circular_shifts,circular_order,p_plus_one


class CandidateSurrogateTests(unittest.TestCase):
    def test_exact_mask_shift_retains_all_rows_and_physical_spacing(self):
        hours=np.arange(1008);hours=hours[~np.isin(hours%24,[5,6])]
        shifts=compatible_circular_shifts(hours)
        self.assertGreater(len(shifts),0)
        s=int(shifts[0]);order=circular_order(hours,s)
        np.testing.assert_array_equal(np.sort(order),np.arange(len(hours)))
        np.testing.assert_array_equal((hours[order]-hours)%1008,np.full(len(hours),s))
        # An irregular gap breaks the periodic missingness mask.
        self.assertEqual(len(compatible_circular_shifts(hours[hours!=400])),0)

    def test_local_donors_are_local_joint_and_reproducible(self):
        z=np.arange(80,dtype=float);neighbours=height_neighbours(z,5)
        order=local_order(neighbours,np.random.default_rng(137))
        np.testing.assert_array_equal(order,local_order(neighbours,np.random.default_rng(137)))
        self.assertTrue(all(j in neighbours[i] for i,j in enumerate(order)))
        theta=np.linspace(-np.pi,np.pi,len(z));direction=np.column_stack([np.cos(theta),np.sin(theta)])
        moved=direction[order]
        np.testing.assert_allclose((moved*moved).sum(axis=1),1)

    def test_empirical_p_keeps_negative_observed_and_plus_one(self):
        self.assertEqual(p_plus_one(-.01,[0,.01]),1)
        self.assertEqual(p_plus_one(.1,[0,.01]),1/3)
        self.assertEqual(p_plus_one(.1,[.1,.01]),2/3)


if __name__=='__main__':unittest.main()
