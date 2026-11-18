import unittest
import numpy as np
from matchms import Spectrum
from matchms.similarity import CosineGreedy
from similarity_api_impl.packed_similarity import PackedReferences


class PackedSimilarityTest(unittest.TestCase):
    def test_scores_and_order_match_matchms(self):
        rng = np.random.default_rng(13)
        spectra = [Spectrum(mz=np.sort(rng.uniform(1, 100, 30)), intensities=rng.uniform(0, 1, 30), metadata={'spectrum_id': str(i)}, metadata_harmonization=False) for i in range(25)]
        # Include equal scores, overlapping tolerance windows, and no-match cases.
        spectra += [Spectrum(mz=np.array([1., 1.05, 2.]), intensities=np.array([1., 1., .5]), metadata={'spectrum_id': str(i)}, metadata_harmonization=False) for i in range(25, 27)]
        packed = PackedReferences(spectra)
        cosine = CosineGreedy()
        for query in spectra:
            expected = np.array([cosine.pair(ref, query)['score'] for ref in spectra])
            keep = np.flatnonzero(expected > 0)
            order = keep[np.argsort(expected[keep])[::-1]]
            actual = packed.score(query.peaks.to_numpy)
            self.assertEqual([x['accession'] for x in actual], [str(i) for i in order])
            np.testing.assert_allclose([x['similarity_score'] for x in actual], expected[order], rtol=1e-12, atol=1e-14)
        self.assertEqual(packed.score(np.array([[1000., 1.]])), [])
        self.assertEqual(packed.score(spectra[0].peaks.to_numpy, ['missing']), [])
        self.assertEqual(len(packed.score(spectra[0].peaks.to_numpy, ['0', '0'])), 1)
        self.assertFalse(packed.peaks.flags.writeable)

    def test_shared_references_are_safe_for_concurrent_queries(self):
        from concurrent.futures import ThreadPoolExecutor
        spectra = [Spectrum(mz=np.array([1., 2., 3.]), intensities=np.array([1., .5, .1]), metadata={'spectrum_id':str(i)}, metadata_harmonization=False) for i in range(20)]
        packed = PackedReferences(spectra)
        query = spectra[0].peaks.to_numpy
        expected = packed.score(query)
        before = packed.peaks.copy()
        with ThreadPoolExecutor(max_workers=8) as pool:
            for result in pool.map(lambda _: packed.score(query), range(64)):
                self.assertEqual(result, expected)
        np.testing.assert_array_equal(packed.peaks, before)

    def test_loader_uses_version_and_loads_only_once(self):
        from pathlib import Path
        from unittest.mock import patch
        from similarity_api_impl.spectra_loader import SpectraLoader

        spectrum = Spectrum(mz=np.array([1., 2.]), intensities=np.array([1., .5]), metadata={'spectrum_id':'example'}, metadata_harmonization=False)
        directory = Path(__file__).with_name("MassBank-test-data")
        loader = SpectraLoader(str(directory))
        with patch('similarity_api_impl.spectra_loader.load_from_massbank_files', return_value=[spectrum]) as load:
            with self.assertLogs("spectra_loader", "INFO") as logs:
                loader.load_spectra()
            snapshot = loader.packed
            loader.load_spectra()
            load.assert_called_once_with(str(directory))
        self.assertIn("0.1.0-test", logs.output[-1])
        self.assertFalse(hasattr(loader, "spectra"))
        self.assertEqual(snapshot.score(spectrum.peaks.to_numpy)[0]['accession'], 'example')
        self.assertIs(loader.packed, snapshot)

    def test_loader_does_not_publish_an_empty_snapshot(self):
        import tempfile
        from similarity_api_impl.spectra_loader import SpectraLoader

        with tempfile.TemporaryDirectory() as directory:
            loader = SpectraLoader(directory)
            with self.assertRaisesRegex(ValueError, "No reference spectra found"):
                loader.load_spectra()
            self.assertIsNone(loader.packed)
