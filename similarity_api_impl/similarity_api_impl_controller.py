import logging
import os
import threading
from datetime import datetime

import connexion
import numpy
from matchms import calculate_scores, set_matchms_logger_level, Spectrum
from matchms.filtering import normalize_intensities
from matchms.importing import load_from_msp
from matchms.similarity import CosineGreedy

from similarity_api.models import SimilarityScore
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

        if request.reference_spectra_list is not None:
            logger.debug("Got %s reference spectra.", len(request.reference_spectra_list))
        references = spectra_loader.spectra
        if request.reference_spectra_list:
            references = [s for s in references if s.metadata['spectrum_id'] in request.reference_spectra_list]
        logger.debug("Use %s for calculation.", len(references))

        scores = calculate_scores(references, [query], CosineGreedy())
        matches = scores.scores_by_query(query, 'CosineGreedy_score', sort=True)
        match_list = SimilarityScoreList(
            [SimilarityScore(match[0].metadata['spectrum_id'], match[1][0]) for match in matches])

        logger.debug("Calculated scores for %s similar spectra.", len(match_list.similarity_score_list))
        return match_list


def version_get():
    """Get the version string of the implementation.

    :rtype: str
    """
    return f'similarity api {__version__}'
