
from pathlib import Path
import re
from pymol import cmd
import os
import warnings
from glob import glob
from pymol import stored
import json
from urllib.request import urlopen


if not hasattr(stored, "alphafold_model_paths"):
    stored.alphafold_model_paths = {}

_model_paths = stored.alphafold_model_paths

def color_plddt(selection="all"):
    plddt_bins = [
        (0, 50, "0xFF7D45"),     # Orange
        (50, 70, "0xFFDB13"),    # Yellow
        (70, 90, "0x65CBF3"),    # Light blue
        (90, 101, "0x0053D6")    # Dark blue
    ]

    # Validate B-factors
    x = cmd.count_atoms(f"({selection}) and (b > 100 or b < 0)")

    if x != 0:
        print(f"Warning: {x} atoms have B-factors outside 0–100 in selection '{selection}'.")
        return

    for lower, upper, color in plddt_bins:
        cmd.color(color, f"({selection}) and not (b < {lower}) and b < {upper}")


cmd.extend("color_plddt", color_plddt)

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
    pae = {"pae": pae_data[0]["predicted_aligned_error"]}

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


def load_af(filename, object='', *args, json_path=None, **kwargs):
    """
    Load an AlphaFold structure and register its confidence JSON.

    Positional arguments follow cmd.load().
    json_path must be specified explicitly by keyword.
    
    returns the object name
    """
    model = Path(filename).expanduser().resolve()

    # Preserve the original cmd.load argument order
    result = cmd.load(filename, object, *args, **kwargs)
    
    object_name = cmd.get_object_list()[-1]
    
    if json_path is None:
        stem = model.stem

        # AlphaFold Server: *_model_N.cif
        match = re.fullmatch(r"(.+)_model_(\d+)", stem)

        if match:
            prefix, index = match.groups()
            json_file = model.with_name(
                f"{prefix}_full_data_{index}.json"
            )

        # Local AlphaFold 3: *_model.cif
        elif stem.endswith("_model"):
            json_file = model.with_name(
                f"{stem[:-6]}_confidences.json"
            )

        else:
            json_file = None

    else:
        json_file = Path(json_path).expanduser()
        if not json_file.is_absolute():
            json_file = model.parent / json_file

    # Register the paths
    if json_file is not None and json_file.is_file():
        _model_paths[object_name] = {
            'model_path' : str(model),
            'data_json' : str(json_file.resolve())
            }
        print(f"AlphaFold JSON: {json_file.name}")
    else:
        _model_paths.pop(object_name, None)
        warnings.warn(
                f"No AlphaFold confidence JSON found for {filename}",
                UserWarning,
                stacklevel=2
            )

    return object_name

cmd.extend("load_af", load_af)


def associate_pae(object, json_path, update=False):
    """
    Associate a file path to the AlphaFold data JSON to an already loaded object.
    """
    if str(update).lower() not in ("true", "false", "0", "1"):
        raise ValueError(f'update must be a boolean expression (True, False, 0, 1), not {update}!')
    else:
        update = str(update).lower() in ("true", "1")

    # Validate, that the object is actually in the session
    if not object in cmd.get_object_list():
        raise ValueError("Object not found!")

    # Validate and normalize JSON path
    json_file = Path(json_path).expanduser().resolve()

    if json_file.is_dir():
        raise IsADirectoryError(f"{json_file} is a directory, not a JSON file!")

    if json_file.suffix.lower() != ".json":
        raise ValueError(f"{json_file} is not a JSON file!")

    if not json_file.is_file():
        raise FileNotFoundError(f"File {json_file} not found!")

    json_path = str(json_file)

    if object in _model_paths:
        # The model is already in the dictionary
        if json_path == _model_paths[object].get('data_json', None):
            # The json path is identical
            print('The data JSON path is already associated to this object!')
        else:
            if update:
                _model_paths[object]['data_json'] = json_path
            else:
                warnings.warn(
                    f"The JSON path differs from the saved:\n"
                    f"SAVED: {_model_paths[object].get('data_json', None)}\n"
                    f"NEW:   {json_path}\n"
                    f"To override, please use update=True",
                    UserWarning
                )

    else:
        _model_paths[object] = {
            'model_path' : None,
            'data_json' : json_path
        }

cmd.extend("associate_pae", associate_pae)


# Autocomplete molecular objects for the first argument
cmd.auto_arg[0]['associate_pae'] = [
    lambda: cmd.Shortcut(cmd.get_object_list()),
    'object',
    ', '
]


def load_alphafold_folder(folder_path, cif_only=True, max_models='ALL', auto_align=True, alignment_selection="ALL", auto_color=True):

    # Validate boolean arguments (PyMOL passes strings)
    def parse_bool(value, name):
        if str(value).lower() in ("true", "1"):
            return True
        elif str(value).lower() in ("false", "0"):
            return False
        else:
            raise ValueError(f"{name} must be True or False.")

    cif_only = parse_bool(cif_only, "cif_only")
    auto_align = parse_bool(auto_align, "auto_align")
    auto_color = parse_bool(auto_color, "auto_color")

    # Validate model count
    if str(max_models).upper() != "ALL":
        try:
            max_models = int(max_models)
        except (ValueError, TypeError):
            raise ValueError(
                "max_models must be 'ALL' (default) or an integer."
            ) from None

        if max_models < 1:
            raise ValueError("max_models must be a positive integer.")

    else:
        max_models = "ALL"

    # Check folder
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder does not exist: {folder_path}")

    files = glob(os.path.join(folder_path, "**"), recursive=True)

    # Only real AlphaFold models should be loaded
    # No templates, and also not the root model of local AlphaFold

    if cif_only:
        file_endings = ['cif']
    else:
        file_endings = ['cif', 'pdb']

    model_files = sorted([n for n in files if any(n.endswith(k) for k in file_endings) and "_model" in n])

    # For home run AlphaFold, there is an additional model in the base.
    # In this case, we want only the models containing seed information
    if any("seed" in n for n in model_files):
        model_files = [n for n in model_files if "seed" in n]

    if max_models != "ALL":
        model_selection = model_files[:max_models]
    else:
        model_selection = model_files

    if not model_selection:
        raise FileNotFoundError(
            f"No AlphaFold models found in {folder_path}"
        )

    object_names = []

    for path in model_selection:
        object_name = load_af(str(path))
        object_names.append(object_name)

    if auto_align:
        anchor = object_names[0]
        for object_name in object_names:
            if object_name == anchor:
                continue

            rmsd_values = cmd.align(f'{object_name} and {alignment_selection}', f'{anchor} and {alignment_selection}')
            rmsd = rmsd_values[0]
            atoms_aligned = rmsd_values[1]
            all_atoms = rmsd_values[4]
            residues_aligned = rmsd_values[6]

            #RMSD =    3.467 (112 atoms)
            print(f'{object_name}, RMSD = {round(rmsd, 2):>8} ({residues_aligned} Residues aligned ({atoms_aligned} / {all_atoms} Atoms))')

    if auto_color:
        for object_name in object_names:
            color_plddt(object_name)


cmd.extend("load_af_folder", load_alphafold_folder)
