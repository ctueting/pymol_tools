# PyMOL Tools

A collection of Python scripts extending [PyMOL](https://pymol.org/) with utilities for structural biology, including AlphaFold model retrieval, confidence-based coloring, PAE visualization, and figure rendering.

## Installation
### Option 1: One-time installation (recommended)

The installer downloads all available tools and combines them into a single Python file (`.pymol_tools.py`) in your home directory.

In the PyMOL command line, enter:

```pymol
run https://ctueting.github.io/pymol_tools/install.py
```

Then install the tools:

```python
install_pymol_tools()
```

If the tools are already installed, you can overwrite the existing installation:

```python
install_pymol_tools(True)
```

To install the tools and automatically load them whenever PyMOL starts:

```python
install_pymol_tools(True, True)
```

The latter also updates your `.pymolrc` configuration file, adding the following entry (with the appropriate path for your operating system):

```pymol
### PyMOL tools START ###
run /path/to/home/.pymol_tools.py
### PyMOL tools END ###
```

The installer works on **macOS, Linux, and Windows**.
**Note:** The tools are stored locally. To update them to the latest version, rerun the installer with `install_pymol_tools(True)`, or use the update command described below. If you have already configured automatic loading, the existing `.pymolrc` entry will continue to work.

### Option 2: Load directly from GitHub Pages

For temporary use without installation, enter:

```pymol
run https://ctueting.github.io/pymol_tools/tools.py
```

This loads all functions referenced by `tools.py` directly from the online repository.

The functions must be loaded again after restarting PyMOL.

### Option 3: Download individual scripts

Alternatively, download only the scripts you want to use.

Drag and drop the downloaded Python files into the PyMOL window, or load them explicitly:

```pymol
run /path/to/display_pae.py
```

To load individual scripts automatically, open **File → Edit pymolrc** and add the corresponding commands:

```pymol
run /path/to/display_pae.py
```

The AlphaFold-related loading, confidence coloring, and JSON-association commands are collected in [`alphafold_utils.py`](alphafold_utils.py); the PAE viewer remains in [`display_pae.py`](display_pae.py). Both files can be loaded separately. The `show_pae` command, however, uses functionality from both files, so load both if you want the combined workflow. **Using the installer or updater is recommended** to ensure that the available tools are loaded together.

## Updates

The collection may be extended with additional tools in the future.

- **Local installation:** Run `update_pymol_tools` in PyMOL to retrieve the latest scripts, overwrite the combined local installation, and register it in `.pymolrc`. To update without changing `.pymolrc`, rerun `install_pymol_tools(True)` after loading `install.py`.
- **Online loading:** Running `tools.py` loads the scripts currently referenced by the online loader.
- **Manual installation:** Download updated scripts individually.

For an installation registered in `.pymolrc`, updated local tools will be loaded automatically the next time PyMOL starts.

## Usage
### `color_plddt` — Color by prediction confidence

Color a structure according to its per-residue pLDDT values stored in the B-factor column:

```pymol
color_plddt my_structure
```

Omitting the selection colors all objects:

```pymol
color_plddt
```

The function applies the conventional AlphaFold pLDDT colors and warns if B-factor values fall outside the range 0–100. **Only use this function when the B-factor column actually contains pLDDT values**: crystallographic B-factors and pLDDT are not interchangeable, even if their numerical ranges overlap.

<img width="473" height="482" alt="Structure colored by pLDDT in PyMOL" src="https://github.com/user-attachments/assets/9e9881b4-2235-4335-8d70-26a8f2bdbbf6" />

### `fetchAF2` — Download AlphaFold structures and PAE data

Download a predicted structure from the [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/) using its UniProt accession:

```pymol
fetchAF2 P12345
```

By default, the structure is downloaded as an mmCIF file into the current working directory and loaded into PyMOL. To request PDB format instead:

```pymol
fetchAF2 P12345, pdb
```

The command now also downloads the corresponding **predicted aligned error (PAE) matrix** and saves it alongside the structure as a `.json` file. The database supplies the matrix under `predicted_aligned_error`; the downloader converts it to the `pae` key in the saved JSON. The original structure is loaded into PyMOL, and both files are retained locally.

You can then apply `color_plddt` to visualize the model confidence.

### `load_af` — Load an AlphaFold model and associate its confidence JSON

`load_af` is a wrapper around PyMOL's standard `load` command, with additional handling for AlphaFold model and confidence-data files. It loads the molecular structure and associates the corresponding confidence JSON, **either implicitly from the AlphaFold naming convention or explicitly via `json_path`**.

```pymol
load_af /path/to/fold_example_4_model_0.cif
```

To specify a JSON file manually (and optionally a PyMOL object name):

```pymol
load_af /path/to/model.cif, my_model, json_path=/path/to/confidence.json
```

Automatic JSON detection supports both AlphaFold Server files (`*_model_N.cif` → `*_full_data_N.json`) and local AlphaFold 3 files (`*_model.cif` → `*_confidences.json`). If no corresponding JSON is found, the structure is **still loaded** and a warning is issued; the model is not registered with a confidence JSON in that case.

#### Shared model-to-JSON registry

The association is kept in **`stored.alphafold_model_paths`**, a dictionary in PyMOL's shared `stored` namespace. Each registered entry is keyed by its PyMOL object name and contains the **absolute paths** to both the original model and its confidence JSON:

```python
stored.alphafold_model_paths["fold_example_4_model_0"] = {
    "model_path": "/absolute/path/fold_example_4_model_0.cif",
    "data_json": "/absolute/path/fold_example_4_full_data_0.json"
}
```

Using `pymol.stored` makes the registry accessible to other loaded scripts **within the same PyMOL session**, rather than keeping separate dictionaries in each script. This is shared runtime state, not a permanent file-based database.

**Important limitation:** PyMOL does not provide a public API for an immutable molecular-object identifier independent of the object name ([PyMOL GitHub discussion #442](https://github.com/schrodinger/pymol-open-source/discussions/442)). Therefore, renaming a PyMOL object after registration **breaks the name-based lookup** unless its registry entry is updated accordingly. Avoid renaming associated objects, or reassociate them under their new names.

### `load_af_folder` — Load an entire AlphaFold prediction folder

`load_af_folder` is a wrapper around `load_af` that **searches recursively** through the specified folder, loads matching model files, and optionally aligns and colors them:

```pymol
load_af_folder /path/to/fold_example_4
```

It handles two common layouts:

- **AlphaFold Server:** The five predicted models (`*_model_0.cif` through `*_model_4.cif`) are located together in one prediction directory.
- **Local AlphaFold 3:** Models are in separate `seed-*_sample-*` subdirectories. If seed-containing models are found, the additional root-level `*_model.cif` is excluded.

By default, only mmCIF files are considered, all matching models are loaded, the models are aligned to the first loaded model, and pLDDT coloring is applied. For example:

```pymol
load_af_folder /path/to/prediction, max_models=5
load_af_folder /path/to/prediction, cif_only=False, auto_align=False, auto_color=False
```

The optional arguments are `cif_only=True`, `max_models=ALL`, `auto_align=True`, `alignment_selection=ALL`, and `auto_color=True`. Set `max_models` to a positive integer to limit the number of models **loaded**.

**Caution — unrestricted recursion:** The current implementation uses recursive `glob` without a maximum directory depth. Selecting an overly broad path may traverse many unrelated folders and load unintended structures. **Always provide the specific AlphaFold prediction directory**, not a parent directory containing multiple projects. `max_models` limits how many matches are loaded, but does not limit the depth of the search. 

### `associate_pae` — Associate or replace the JSON of an existing object

Use `associate_pae` when a model was loaded with PyMOL's regular `load` command or when you want to register a different confidence JSON:

```pymol
load /path/to/model.cif, my_model
associate_pae my_model, /path/to/confidence.json
```

For an object already registered with a different JSON, the existing association is retained and a warning is issued. To replace it explicitly:

```pymol
associate_pae my_model, /path/to/updated_confidence.json, update=True
```

The command requires an existing PyMOL molecular object and a real `.json` file (not a directory). JSON paths are normalized to absolute paths and saved in `stored.alphafold_model_paths`. This checks the file path and extension, but **does not validate the contents of the JSON**.

### `signature` — Custom rendering signature

Apply my custom PyMOL rendering settings for publication-quality figures:

```pymol
signature
```

This signature has been used in my published figures, for example in [Nature Communications (2025)](https://doi.org/10.1038/s41467-025-65159-3).

<img width="792" height="388" alt="Example molecular rendering with the custom PyMOL signature" src="https://github.com/user-attachments/assets/44d30709-d59a-4777-81d0-07e8c46a7694" />
*Note: The default molecular colors were additionally adjusted in this example.*

### `display_pae` — Interactive AlphaFold PAE viewer

Display a predicted aligned error (PAE) matrix from an AlphaFold confidence JSON file:

```pymol
display_pae /path/to/confidence.json
```

The command opens a separate Qt window with the PAE matrix. **You do not need to load the corresponding structure** to visualize or export its PAE plot.
<img width="1042" height="878" alt="Interactive PAE matrix viewer with palette selector and export options" src="https://github.com/user-attachments/assets/1208af44-e95c-48d5-8274-f2b5968f0d6b" />
The viewer provides selectable color palettes, chain-boundary separators (where chain metadata are available), and a fixed 0–31 Å PAE color scale. Figures can be exported as **300 dpi PNG**, **PDF**, or **SVG**. The PDF and SVG exports use vector graphics for annotations, axes, and the colorbar; the PAE matrix itself is raster-based.

#### Link the PAE matrix to a PyMOL structure

To explore which regions correspond to a PAE block, load the matching predicted structure in PyMOL and select it from the **Associate object** dropdown in the PAE window. Click and drag to draw a rectangular region on the matrix. The corresponding residues are selected and highlighted in the structure, while the remaining structure is colored grey. Use **Restore colors** to recover the original molecular colors.
<img width="1512" height="879" alt="PAE region selection linked to a molecular structure in PyMOL" src="https://github.com/user-attachments/assets/b58e89d5-1610-4779-991b-f9d6d729b779" />

For multichain predictions, correct residue selection requires the confidence JSON to contain the necessary token-to-chain/residue metadata and the associated PyMOL object to correspond to that prediction. PAE values express predicted alignment error, not experimental distance or direct evidence of an interaction.
**Requirements:** `display_pae` uses NumPy and PyMOL's bundled Qt interface. SVG export also requires the Qt SVG module (`PyQt5.QtSvg` in the tested PyMOL build). No Matplotlib or Seaborn installation is required.

### `show_pae` — Open the PAE associated with a loaded object

`show_pae` combines the shared model registry maintained by `alphafold_utils.py` with the viewer in `display_pae.py`. Instead of providing a JSON path, supply the name of a registered PyMOL object:

```pymol
show_pae fold_example_4_model_0
```

The command looks up the confidence JSON associated with that object and passes it to the PAE viewer. **If the object has no registered JSON**, it raises a `ValueError` with instructions to use `associate_pae` first. If the object has been renamed since registration, the name-based association will also need to be updated.

**Module organization:** `alphafold_utils.py` and `display_pae.py` are intentionally kept as separate scripts because model loading/coloring and PAE visualization are useful independently. The integrated `show_pae` workflow requires both. For the most reliable setup, use `install_pymol_tools` / `update_pymol_tools` rather than manually loading selected scripts.

## Combined script

The repository contains [`tools.py`](tools.py), a small loader that retrieves the individual tools from the online repository. It may be extended with additional scripts in the future.

Using the online loader makes future additions and updates available without downloading the individual files again.

## Author

**Christian Tüting**

## License

This project is distributed under the [MIT License](LICENSE). You may use, modify, and redistribute the code, including for commercial purposes. **No scientific citation is required by the license**, but redistributions or substantial copies must retain the copyright and license notices.

## Disclaimer

This repository is an independent collection of utilities for research and visualization. The author is **not affiliated with or endorsed by Google DeepMind, AlphaFold, EMBL-EBI, UniProt, or Schrödinger**. All product names and trademarks belong to their respective owners.
