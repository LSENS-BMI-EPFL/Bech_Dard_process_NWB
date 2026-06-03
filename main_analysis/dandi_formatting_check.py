from pynwb import NWBHDF5IO
import glob
import os
import re
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

DIR = r"Z:\publications\2026\2026_Bech_Dard_eLife\2026_Bech_Dard_eLife_data\001847"
nwb_files = sorted(glob.glob(os.path.join(DIR, "*", "*.nwb")), key=natural_sort_key)
publication = 'https://elifesciences.org/reviewed-preprints/109717'

issues = []

for nwb_file in tqdm(nwb_files, desc="Checking files"):
    try:
        with NWBHDF5IO(nwb_file, 'r') as io:
            nwb_data = io.read()
            pub_ok = publication in nwb_data.related_publications
            weight = nwb_data.subject.weight
            weight_ok = weight and weight != 'na' and weight.endswith(' g')

            if not pub_ok or not weight_ok:
                issues.append(os.path.basename(nwb_file))
                tqdm.write(f"[ISSUE] {os.path.basename(nwb_file)} | pub={pub_ok} | weight='{weight}'")
            else:
                tqdm.write(f"[OK] {os.path.basename(nwb_file)} | pub={nwb_data.related_publications}; {pub_ok} | weight='{weight}'")
    except Exception as e:
        tqdm.write(f"Failed {os.path.basename(nwb_file)}: {e}")

tqdm.write(f"\n{len(issues)} files with issues out of {len(nwb_files)}")