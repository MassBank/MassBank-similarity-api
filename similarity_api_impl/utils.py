import os
import numpy as np
from matchms import Spectrum

def load_from_massbank_files(dir: str) -> list[Spectrum]:
    files = list_files_recursive(dir)
    spectra = list[Spectrum]()
    for i, file in enumerate(files):
        # print(f'--> Processing file {i + 1}/{len(files)} -> {file}')
        with open(file, 'r') as f:
            lines = f.readlines()
            accession = None
            precursor_mz = None
            precursor_type = None
            num_peaks = None
            peak_line_index = None
            peak_line_visited_count = 0
            masses = np.array([])
            rel_intensities = np.array([])
            is_deprecated = False
            for j, line in enumerate(lines):
                if line.startswith('DEPRECATED:'):
                     is_deprecated = True
                     break
                if line.startswith('ACCESSION:'):
                        accession = line.split(':')[1].strip()
                if line.startswith('MS$FOCUSED_ION: PRECURSOR_M/Z'):
                        precursor_mz = line.split(' ')[2].strip()
                if line.startswith('MS$FOCUSED_ION: PRECURSOR_TYPE'):
                        precursor_type = line.split(' ')[2].strip()
                if peak_line_index is None:
                    if line.startswith('PK$NUM_PEAK:'):
                        num_peaks = line.split(':')[1].strip()                        
                    if line.startswith('PK$PEAK:'):
                        peak_line_index = j + 1
                else:
                    if peak_line_visited_count < int(num_peaks):
                        peak_line_split = lines[j].strip().split(" ")
                        masses = np.append(masses, float(peak_line_split[0]))
                        rel_intensities = np.append(rel_intensities, float(peak_line_split[2]))
                        peak_line_visited_count += 1
                    else:
                        break
            if is_deprecated:
                # print(f'Processing file {file} -> Skipping to next file because it is deprecated.')
                continue          

            # Create Spectrum objects from the extracted data
            spectrum = Spectrum(mz=masses,
                            intensities=rel_intensities,
                            metadata={"spectrum_id": accession, 
                                      "precursor_mz": precursor_mz,
                                      "precursor_type": precursor_type})
            spectra.append(spectrum)

    return spectra

def list_files_recursive(path) -> list[str]:
    files = list()
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            files.extend(list_files_recursive(full_path))
        elif 'MSBNK-' in full_path and full_path.endswith('.txt'):
                files.append(full_path)
    return files