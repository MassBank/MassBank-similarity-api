import os
from typing import Any, Generator
import numpy as np
from matchms import Spectrum


def load_from_massbank_files(directory: str) -> list[Spectrum]:
    files = list_files_recursive(directory)
    spectra = list[Spectrum]()
    for i, file in enumerate(files):
        # print(f'--> Processing file {i + 1}/{len(files)} -> {file}')
        with open(file, 'r') as f:
            lines = f.readlines()
        metadata = {}
        masses, rel_intensities = [], []
        is_deprecated = False
        num_peaks, peak_line_index = None, None
        for j, line in enumerate(lines):
            if line.startswith('DEPRECATED:'):
                is_deprecated = True
                break
            if line.startswith('ACCESSION:'):
                metadata["spectrum_id"] = line.split(':')[1].strip()
            elif line.startswith('MS$FOCUSED_ION: PRECURSOR_M/Z'):
                metadata["precursor_mz"] = line.split(' ')[2].strip()
            elif line.startswith('MS$FOCUSED_ION: PRECURSOR_TYPE'):
                metadata["precursor_type"] = line.split(' ')[2].strip()
            elif line.startswith('PK$NUM_PEAK:'):
                num_peaks = int(line.split(':')[1].strip())
            elif peak_line_index is None:
                if line.startswith('PK$PEAK:'):
                    # Start collecting peaks from the next line
                    peak_line_index = j + 1
            elif j >= peak_line_index and len(masses) < num_peaks:
                peak_data = line.strip().split(" ")
                masses.append(float(peak_data[0]))
                rel_intensities.append(float(peak_data[2]))

        if is_deprecated:
            # print(f'Processing file {file} -> Skipping to next file because it is deprecated.')
            continue

        spectrum = Spectrum(
            mz=np.array(masses),
            intensities=np.array(rel_intensities),
            metadata=metadata,
        )
        spectra.append(spectrum)

    return spectra


def list_files_recursive(path: str) -> Generator[str, Any | None, None]:
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            yield from list_files_recursive(full_path)
        elif 'MSBNK-' in full_path and full_path.endswith('.txt'):
            yield full_path