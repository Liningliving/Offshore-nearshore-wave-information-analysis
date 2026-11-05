"""Runtime test of the compiled official Java estimator's temporal exclusion."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAR=ROOT/'tools/jidt/build/infodynamics.jar'


@unittest.skipUnless(JAR.exists(),'Build official JIDT first; skipped tests are not integration proof')
class ExactJavaIntegration(unittest.TestCase):
    def test_actual_java_masks_metadata_settings_and_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            files=['ElapsedHourLoader.java','SharedEstimatorSettings.java','ExactTheilerIntegrationCheck.java']
            subprocess.run(['javac','-cp',str(JAR),'-d',tmp,*[str(ROOT/'src/java'/f) for f in files]],check=True,capture_output=True)
            subprocess.run(['java','-cp',tmp+':'+str(JAR),'ExactTheilerIntegrationCheck',tmp],check=True,capture_output=True)
            evidence=json.loads((Path(tmp)/'java_results.json').read_text())
            self.assertTrue(evidence['exact_45_hour_integration_passed'])
            self.assertEqual(evidence['mismatches'],0)
            self.assertEqual(evidence['observations'],241)
            self.assertEqual(evidence['boundary_hours_tested'],[44,45,46])
            self.assertTrue(evidence['different_set_short_gap_bypass_verified_mi_and_cmi'])


if __name__=='__main__': unittest.main()
