"""Regression checks for references embedded in unmodified historical artifacts."""
import json
from pathlib import Path
import sys
import unittest
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from artifact_paths import ROOT,resolve_artifact_path

class HistoricalArtifactPaths(unittest.TestCase):
    def test_directory_absolute_and_exact_file_mapping(self):
        self.assertEqual(resolve_artifact_path('outputs/step7/primary_information_summary.csv'),ROOT/'results/primary_information/primary_information_summary.csv')
        self.assertEqual(resolve_artifact_path(ROOT/'outputs/step8/significance_summary.csv'),ROOT/'research/surrogate_validation/wave_significance_status.csv')
        self.assertEqual(resolve_artifact_path('outputs/step9extra/file.csv'),ROOT/'outputs/step9extra/file.csv')
        self.assertEqual(resolve_artifact_path('/private/tmp/unrelated.csv'),Path('/private/tmp/unrelated.csv'))
        self.assertEqual(resolve_artifact_path('results/primary_information/report.md'),ROOT/'results/primary_information/report.md')

    def test_all_archived_surrogate_result_references_resolve(self):
        d=pd.read_csv(ROOT/'research/surrogate_validation/validation/synthetic_results.csv')
        self.assertEqual(len(d),192)
        for value in d.output_file:self.assertTrue(resolve_artifact_path(value).is_file(),value)

    def test_verified_scientific_source_hashes_still_match(self):
        import hashlib
        d=json.loads((ROOT/'config/verified_sources.json').read_text())
        for old,digest in d['sources_sha256'].items():
            self.assertEqual(hashlib.sha256(resolve_artifact_path(old).read_bytes()).hexdigest(),digest)

if __name__=='__main__':unittest.main()
