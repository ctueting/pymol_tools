
# PyMOL Tools

A small collection of Python scripts extending [PyMOL](https://pymol.org/) with additional functions for structural biology, AlphaFold structure retrieval, coloring, and rendering.

## Installation

### Option 1: Run directly (recommended)

Open PyMOL and enter the following command:

```python
run https://ctueting.github.io/pymol_tools/tools.py
```

This loads all custom functions directly from the online repository without downloading or installing anything.

**Note:** The functions must be loaded again whenever PyMOL is restarted.

### Option 2: Download and run locally

Download the following three Python files from this repository:

- `color_plddt.py`
- `fetchAF2.py`
- `pymol_sig.py`

Simply drag and drop the files into the PyMOL window to load the corresponding functions.

### Option 3: Load automatically using `.pymolrc`

To make the custom functions available automatically whenever PyMOL starts, add them to your `.pymolrc` configuration file.

1. Download the three Python files and save them anywhere on your computer.
2. In PyMOL, navigate to **File → Edit pymolrc**.
3. Add the following lines, replacing the paths with the actual file locations:

```python
run /path/to/color_plddt.py
run /path/to/fetchAF2.py
run /path/to/pymol_sig.py
```

Save the file and restart PyMOL. All functions will now be loaded automatically.

Alternatively, add just the online version to `.pymolrc`:

```python
run https://ctueting.github.io/pymol_tools/tools.py
```

This automatically loads the latest online version whenever PyMOL starts, provided an internet connection is available.

## Combined script

The repository also contains `tools.py`, which combines the three individual scripts into a single file for convenience.

**Note:** The combined `tools.py` may be extended with additional tools and functions in the future. Using the online version ensures access to the latest additions and updates.

## Author

Christian Tüting
