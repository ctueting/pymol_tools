# PyMOL Tools

A collection of Python scripts extending [PyMOL](https://pymol.org/) with utilities for structural biology, including AlphaFold model retrieval, confidence-based coloring, PAE visualization, and figure rendering.

## Installation

### Option 1: Load directly from GitHub Pages (recommended)

Enter the following command in the PyMOL command line:

```pymol
run https://ctueting.github.io/pymol_tools/tools.py
```

This loads the functions included in `tools.py` without manually downloading their individual scripts. The functions must be loaded again after restarting PyMOL.

### Option 2: Download and run locally

Download the scripts you want to use:

- [`color_plddt.py`](color_plddt.py) — color structures by pLDDT.
- [`fetchAF2.py`](fetchAF2.py) — retrieve structures from the AlphaFold Protein Structure Database.
- [`pymol_sig.py`](pymol_sig.py) — apply a custom rendering signature.
- [`display_pae.py`](display_pae.py) — display and interact with AlphaFold PAE matrices.

Drag and drop each Python file into the PyMOL window, or load it explicitly:

```pymol
run /path/to/display_pae.py
```

### Option 3: Load automatically with `.pymolrc`

To make the functions available whenever PyMOL starts, open **File → Edit pymolrc** and add the paths to your locally saved scripts:

```pymol
run /path/to/color_plddt.py
run /path/to/fetchAF2.py
run /path/to/pymol_sig.py
run /path/to/display_pae.py
```

Alternatively, add the online loader to `.pymolrc`:

```pymol
run https://ctueting.github.io/pymol_tools/tools.py
```

This loads the latest version of the scripts referenced by `tools.py` at startup, provided an internet connection is available.

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
