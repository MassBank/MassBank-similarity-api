import logging
import os
import threading
from datetime import datetime
from matchms.importing import load_from_msp

logger = logging.getLogger('spectra_loader')

class SpectraLoader:
    def __init__(self, msp_file):
        self.msp_file = msp_file
        self.timestamp = datetime.min
        self.spectra = []
        self.lock = threading.Lock()

    def load_spectra(self):
        """Load all spectra from the given msp file"""
        with self.lock:
            file_timestamp = datetime.fromtimestamp(os.path.getmtime(self.msp_file))
            logger.debug("In-memory timestamp of reference spectra: %s", self.timestamp)
            logger.debug("Reference spectra data file timestamp: %s", file_timestamp)
            if file_timestamp > self.timestamp:
                logger.info("Loading spectra from %s.", self.msp_file)
                self.spectra = list(load_from_msp(self.msp_file))
                self.timestamp = file_timestamp
                logger.info("Loaded %s spectra.", len(self.spectra))

# Environment variables
MSP = os.environ.get('MSP', "./MassBank_NIST.msp")
# Global instance
spectra_loader = SpectraLoader(MSP)