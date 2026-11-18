import logging
import os
from pathlib import Path

from similarity_api_impl.packed_similarity import PackedReferences
from similarity_api_impl.massbank_utils import load_from_massbank_files

logger = logging.getLogger('spectra_loader')

class SpectraLoader:
    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.packed: PackedReferences | None = None

    def load_spectra(self) -> None:
        """Build and publish the snapshot during single-writer startup."""
        if self.packed is not None:
            return

        data_dir = self.data_dir
        if data_dir is None:
            data_dir = Path(os.environ.get("DATA_DIR", "./MassBank-data"))
        version_file = data_dir / "VERSION"
        try:
            metadata = version_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            version = "unversioned"
        else:
            fields = (line.split("=", 1) for line in metadata.splitlines() if "=" in line)
            version = next((value.strip() for key, value in fields if key.strip() == "version"), "")
            if not version:
                raise ValueError(f"No dataset version in {version_file}")

        logger.info("Loading reference spectra from %s (dataset %s).", data_dir, version)
        spectra = load_from_massbank_files(str(data_dir))
        if not spectra:
            raise ValueError(f"No reference spectra found in {data_dir}")
        self.packed = PackedReferences(spectra)
        logger.info("Loaded %s reference spectra (dataset %s).", len(spectra), version)


spectra_loader = SpectraLoader()
