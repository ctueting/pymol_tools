import json
from pathlib import Path
from urllib.request import urlopen
from pymol import cmd


def download_alphafold(uniprot_id, fmt="cif"):
    """Download the latest AlphaFold DB structure for a UniProt ID."""

    fmt = fmt.lower()

    if fmt not in ("cif", "pdb"):
        raise ValueError("Format must be 'cif' or 'pdb'.")

    api = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"

    # Retrieve structure metadata
    with urlopen(api, timeout=30) as response:
        data = json.load(response)

    if not data:
        raise ValueError(f"No AlphaFold structure found for {uniprot_id}.")

    # Select structure format
    url = data[0]["pdbUrl" if fmt == "pdb" else "cifUrl"]

    # Download structure
    filename = Path(f"{uniprot_id}.{fmt}")

    with urlopen(url, timeout=120) as response:
        filename.write_bytes(response.read())

    return filename


def fetchAF2(uniprot_id, fmt="cif"):
    """Download and load an AlphaFold structure into PyMOL."""

    try:
        filename = download_alphafold(uniprot_id, fmt)

        print(
            f"The file was downloaded and saved here: "
            f"{filename.resolve()}"
        )

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
