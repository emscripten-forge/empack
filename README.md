# empack

Pack a mamba environment with emsdk

## Installation

```bash
mamba install empack -c conda-forge
```

or with pip:

```bash
pip install empack
```

## Usage

You can pack the Python 3.10 environment (located at `/path/to/env`) with the following command:

```bash
empack pack python core /path/to/env --version=3.10
```

This will generate two files `python_data.js` and `python_data.data` that you can use in the browser.
