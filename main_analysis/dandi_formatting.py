from pynwb import NWBHDF5IO
import h5py
import glob
import os
import re
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def fix_broken_acquisitions(nwb_file):
    """Remove dangling acquisition links using h5py, returns list of removed keys."""
    removed = []
    with h5py.File(nwb_file, 'r+') as f:
        if '/acquisition' not in f:
            return removed
        for key in list(f['/acquisition'].keys()):
            try:
                _ = f['/acquisition'][key][()]
            except Exception:
                del f['/acquisition'][key]
                removed.append(key)
    return removed

def needs_fixing(nwb_file, publication):
    """Check if the file needs metadata fixing."""
    with NWBHDF5IO(nwb_file, "r") as io:
        nwb_data = io.read()
        pub_ok = publication in nwb_data.related_publications
        weight = nwb_data.subject.weight
        weight_ok = weight and weight != 'na' and weight.endswith('g')
    return not pub_ok or not weight_ok


DIR = r"Z:\publications\2026\2026_Bech_Dard_eLife\2026_Bech_Dard_eLife_data\001847"
nwb_files = sorted(glob.glob(os.path.join(DIR, "*", "*.nwb")), key=natural_sort_key)
publication = 'https://elifesciences.org/reviewed-preprints/109717'

# --- Pass 1: fix broken acquisitions ---
tqdm.write("=== Pass 1: Fixing broken acquisitions ===")
for nwb_file in tqdm(nwb_files, desc="Scanning acquisitions"):
    try:
        removed = fix_broken_acquisitions(nwb_file)
        if removed:
            tqdm.write(f"Removed {removed} from {os.path.basename(nwb_file)}")
    except Exception as e:
        tqdm.write(f"h5py failed on {os.path.basename(nwb_file)}: {e}")

# --- Pass 2: fix metadata, skip already-fixed files ---
tqdm.write("=== Pass 2: Fixing metadata ===")
for nwb_file in tqdm(nwb_files, desc="Fixing metadata"):
    try:
        if not needs_fixing(nwb_file, publication):
            continue

        with NWBHDF5IO(nwb_file, "r+") as io:
            nwb_data = io.read()
            subject_data = nwb_data.subject

            if publication not in nwb_data.related_publications:
                nwb_data.fields['related_publications'] = (publication,)

            weight = subject_data.weight
            if not weight or weight == 'na':
                subject_data.fields['weight'] = '0g'
            elif not weight.endswith('g'):
                subject_data.fields['weight'] = f'{weight}g'

            io.write(nwb_data)

    except Exception as e:
        tqdm.write(f"Skipping {os.path.basename(nwb_file)}: {e}")