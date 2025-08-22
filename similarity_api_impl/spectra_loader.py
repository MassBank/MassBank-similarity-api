import logging
import os
import threading
from datetime import datetime
from similarity_api_impl.utils import load_from_massbank_files

logger = logging.getLogger('spectra_loader')

class SpectraLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.timestamp = datetime.min
        self.spectra = []
        self.lock = threading.Lock()

    def load_spectra(self):
        """Load all spectra from the given msp file"""
        with self.lock:
            file_timestamp = datetime.fromtimestamp(os.path.getmtime(self.data_dir))
            logger.debug("In-memory timestamp of reference spectra: %s", self.timestamp)
            logger.debug("Reference spectra data file timestamp: %s", file_timestamp)
            if file_timestamp > self.timestamp:
                logger.info("Loading spectra from %s.", self.data_dir)
                self.spectra = load_from_massbank_files(self.data_dir)                
                self.timestamp = file_timestamp
                logger.info("Loaded %s spectra from %s.", len(self.spectra), self.data_dir)

# Environment variables
DATA_DIR = os.environ.get('DATA_DIR', "./MassBank-data")
# Global instance
spectra_loader = SpectraLoader(DATA_DIR)

