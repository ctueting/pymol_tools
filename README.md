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

**Note:** The tools are stored locally. To update them to the latest version, simply rerun the installer with `install(True)`. If you have already configured automatic loading, the existing `.pymolrc` entry will continue to work.

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

## Updates

The collection may be extended with additional tools in the future.

- **Local installation:** Run `update_pymol_tools True, True` to fetch the latest file, overwrite the local copy, and update pymolrc
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

### `fetchAF2` — Download AlphaFold structures

Download a predicted structure from the [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/) using its UniProt accession:

```pymol
fetchAF2 P12345
```

By default, the structure is downloaded as an mmCIF file into the current working directory and loaded into PyMOL. To request PDB format instead:

```pymol
fetchAF2 P12345, pdb
```

You can then apply `color_plddt` to visualize the model confidence.

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

## Combined script

The repository contains [`tools.py`](tools.py), a small loader that retrieves the individual tools from the online repository. It may be extended with additional scripts in the future.

Using the online loader makes future additions and updates available without downloading the individual files again.

## Author

**Christian Tüting**

## Disclaimer

This repository is an independent collection of utilities for research and visualization. The author is **not affiliated with or endorsed by Google DeepMind, AlphaFold, EMBL-EBI, UniProt, or Schrödinger**. All product names and trademarks belong to their respective owners.
