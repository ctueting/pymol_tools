
import json
from pathlib import Path
from urllib.request import urlopen
from pymol import cmd


def download_alphafold(uniprot_id, fmt="cif"):
    """Download an AlphaFold DB structure and its PAE matrix."""

    fmt = fmt.lower()

    if fmt not in ("cif", "pdb"):
        raise ValueError("Format must be 'cif' or 'pdb'.")

    api = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"

    # Retrieve structure metadata
    with urlopen(api, timeout=30) as response:
        data = json.load(response)

    if not data:
        raise ValueError(f"No AlphaFold structure found for {uniprot_id}.")

    prediction = data[0]

    # Download structure
    url = prediction["pdbUrl" if fmt == "pdb" else "cifUrl"]
    filename = Path(f"{uniprot_id}.{fmt}")

    with urlopen(url, timeout=120) as response:
        filename.write_bytes(response.read())

    # Download PAE matrix
    with urlopen(prediction["paeDocUrl"], timeout=120) as response:
        pae_data = json.load(response)

    # Convert AlphaFold DB format to AlphaFold 3 format
    pae = {"PAE": pae_data[0]["predicted_aligned_error"]}

    # Save converted PAE JSON
    json_filename = filename.with_suffix(".json")

    with json_filename.open("w") as f:
        json.dump(pae, f, separators=(",", ":"))

    return filename


def fetchAF2(uniprot_id, fmt="cif"):
    """Download and load an AlphaFold structure into PyMOL."""

    try:
        filename = download_alphafold(uniprot_id, fmt)

        print(f"Structure saved: {filename.resolve()}")
        print(f"PAE saved:       {filename.with_suffix('.json').resolve()}")

    except Exception as e:
        print(
            f"\nThe structure for {uniprot_id} could not be downloaded.\n"
            f"Please see the error log for details:\n\n{e}\n"
        )
        return None

    # Load structure into PyMOL
    cmd.load(str(filename))

    return str(filename)


cmd.extend("fetchAF2", fetchAF2)
