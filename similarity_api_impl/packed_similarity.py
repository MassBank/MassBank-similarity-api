"""Read-only reference arrays shared by all request threads in this process."""
import numpy as np
from numba import njit
from matchms.similarity.spectrum_similarity_functions import collect_peak_pairs, score_best_matches


@njit(nogil=True, cache=True)
def cosine_scores(peaks, offsets, query, indices):
    scores = np.zeros(len(indices), dtype=np.float64)
    for i in range(len(indices)):
        ref = indices[i]
        spectrum = peaks[offsets[ref]:offsets[ref + 1]]
        pairs = collect_peak_pairs(spectrum, query, 0.1, 0.0, 0.0, 1.0)
        if pairs is not None:
            pairs = pairs[np.argsort(pairs[:, 2], kind='mergesort')[::-1], :]
            scores[i] = score_best_matches(pairs, spectrum, query, 0.0, 1.0)[0]
    return scores


class PackedReferences:
    def __init__(self, spectra):
        self.accessions = tuple(s.metadata['spectrum_id'] for s in spectra)
        self.offsets = np.zeros(len(spectra) + 1, dtype=np.int64)
        for i, spectrum in enumerate(spectra):
            self.offsets[i + 1] = self.offsets[i] + len(spectrum.peaks)
        self.peaks = np.empty((self.offsets[-1], 2), dtype=np.float64)
        for i, spectrum in enumerate(spectra):
            self.peaks[self.offsets[i]:self.offsets[i + 1]] = spectrum.peaks.to_numpy
        self.peaks.flags.writeable = False
        self.offsets.flags.writeable = False
        # Compile before readiness; subsequent requests only execute native code.
        dummy = np.array([[1.0, 1.0], [2.0, 1.0]])
        for query in (dummy, np.asfortranarray(dummy)):
            cosine_scores(self.peaks, self.offsets, query, np.empty(0, dtype=np.int64))

    def score(self, query, accessions=None):
        if accessions:
            selected = set(accessions)
            indices = np.array([i for i, name in enumerate(self.accessions) if name in selected], dtype=np.int64)
        else:
            indices = np.arange(len(self.accessions), dtype=np.int64)
        scores = cosine_scores(self.peaks, self.offsets, query, indices)
        # Match matchms' nonzero filtering and descending NumPy argsort semantics.
        positive = np.flatnonzero(scores > 0)
        order = positive[np.argsort(scores[positive])[::-1]]
        return [{'accession': self.accessions[indices[i]], 'similarity_score': float(scores[i])} for i in order]
