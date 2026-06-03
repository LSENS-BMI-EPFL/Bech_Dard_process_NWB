import h5py
import glob
import os
import re
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def needs_fixing(f, publication):
    pub = f['/general/related_publications'][()].tolist()
    pub = [p.decode('utf-8') if isinstance(p, bytes) else p for p in pub]
    pub_ok = publication in pub

    if '/general/subject/weight' in f:
        weight = f['/general/subject/weight'][()].decode('utf-8')
        weight_ok = weight and weight != 'na' and weight.endswith(' g')
    else:
        weight_ok = False

    return not pub_ok or not weight_ok


DIR = r"Z:\publications\2026\2026_Bech_Dard_eLife\2026_Bech_Dard_eLife_data\001847"
nwb_files = sorted(glob.glob(os.path.join(DIR, "*", "*.nwb")), key=natural_sort_key)
publication = 'https://elifesciences.org/reviewed-preprints/109717'

# --- Pass 1: fix broken acquisitions ---
tqdm.write("=== Pass 1: Fixing broken acquisitions ===")
for nwb_file in tqdm(nwb_files, desc="Scanning acquisitions"):
    try:
        with h5py.File(nwb_file, 'r+') as f:
            if '/acquisition' not in f:
                continue
            for key in list(f['/acquisition'].keys()):
                try:
                    _ = f['/acquisition'][key][()]
                except Exception:
                    del f['/acquisition'][key]
                    tqdm.write(f"Removed '{key}' from {os.path.basename(nwb_file)}")
    except Exception as e:
        tqdm.write(f"h5py failed on {os.path.basename(nwb_file)}: {e}")

# --- Pass 2: fix metadata ---
tqdm.write("=== Pass 2: Fixing metadata ===")
for nwb_file in tqdm(nwb_files, desc="Fixing metadata"):
    try:
        with h5py.File(nwb_file, 'r+') as f:
            if not needs_fixing(f, publication):
                continue

            # Fix related_publications
            pub = f['/general/related_publications'][()].tolist()
            pub = [p.decode('utf-8') if isinstance(p, bytes) else p for p in pub]
            if publication not in pub:
                del f['/general/related_publications']
                f['/general'].create_dataset('related_publications', data=[publication])
                tqdm.write(f"Publication fixed for {os.path.basename(nwb_file)}")

            # Fix weight
            if '/general/subject/weight' in f:
                weight = f['/general/subject/weight'][()].decode('utf-8')
                del f['/general/subject/weight']
            else:
                weight = None

            if not weight or weight == 'na':
                new_weight = '0 g'
            elif not weight.endswith(' g'):
                new_weight = f'{weight.rstrip("g").strip()} g'
            else:
                new_weight = None

            if new_weight:
                f['/general/subject'].create_dataset('weight', data=new_weight)
                tqdm.write(f"Weight: '{weight}' -> '{new_weight}' for {os.path.basename(nwb_file)}")
    except Exception as e:
        tqdm.write(f"Skipping {os.path.basename(nwb_file)}: {e}")