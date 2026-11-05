import requests
from pathlib import Path


def download_alphafold(uniprot_id, fmt="cif"):
    """Download the latest AlphaFold DB structure for a UniProt ID."""
    api = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"

    response = requests.get(api, timeout=30)
    response.raise_for_status()

    data = response.json()[0]
    url = data["pdbUrl" if fmt == "pdb" else "cifUrl"]

    filename = f"{uniprot_id}.{fmt}"
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename


def fetchAF2(uniprot_id, fmt="cif"):
    # Download the latest structure from the AlphaFold DB
    try:
        filename = download_alphafold(uniprot_id, fmt)
        print(f"The file was downloaded and saved here: {Path(filename).resolve()}")
    except Exception as e:
        print(f"""
The structure for {uniprot_id} could not be downloaded.
Please see the error log for details:

{e}
""")
        return None

    # Open the structure
    cmd.load(filename)


cmd.extend("fetchAF2", fetchAF2)
