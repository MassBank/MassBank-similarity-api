import logging
import os

import connexion
import numpy
from matchms import set_matchms_logger_level, Spectrum
from matchms.filtering import normalize_intensities

from similarity_api.models.similarity_calculation import SimilarityCalculation
from similarity_api.models.similarity_score_list import SimilarityScoreList
from similarity_api_impl.spectra_loader import spectra_loader
from similarity_api_impl.version import __version__

# Environment variables
VERBOSE = os.environ.get('VERBOSE', "false")

# set log level
set_matchms_logger_level("ERROR")

logger = logging.getLogger('similarity_api_impl_controller')
if VERBOSE == "true":
    logger.setLevel(logging.DEBUG)

def similarity_post(similarity_calculation):
    """Create a new similarity calculation.

    :param similarity_calculation: a similarity job
    :type similarity_calculation: SimilarityCalculation

    :rtype: SimilarityScoreList
    """
    if connexion.request.is_json:
        request = SimilarityCalculation.from_dict(similarity_calculation)

        spectra_loader.load_spectra()

        mz, intensities = zip(*[(peak.mz, peak.intensity) for peak in request.peak_list])
        logger.debug("Got spectra: %s", request.peak_list)

        try:
            query = normalize_intensities(Spectrum(mz=numpy.array(mz), intensities=numpy.array(intensities)))
        except AssertionError as e:
            return connexion.problem(
                title="AssertionError",
                detail=str(e),
                status=400,
            )

        # Keep one immutable snapshot for the duration of this request.
        packed = spectra_loader.packed
        return SimilarityScoreList.from_dict({
            "similarity_score_list": packed.score(query.peaks.to_numpy, request.reference_spectra_list)
        })
    return None


def version_get():
    """Get the version string of the implementation.

    :rtype: str
    """
    return f'similarity api {__version__}'
