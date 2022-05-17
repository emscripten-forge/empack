# emboa

Pack a mamba environment with emsdk

## Requirements

You first need to setup emsdk:

```bash
mamba install -c conda-forge emsdk
emsdk install 3.1.2
emsdk activate 3.1.2
```

## Installation

```bash
pip install git+https://github.com/emscripten-forge/emboa
```

## Usage

You can pack the Python 3.10 environment (located at `/path/to/env`) with the following command:

```bash
emboa pack python core /path/to/env --version=3.10
```

This will generate two files `python_data.js` and `python_data.data` that you can use in the browser.
