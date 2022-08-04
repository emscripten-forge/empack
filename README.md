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

You can pack the  environment (located at `/path/to/env`) with the following command:

```bash
empack pack env --env-prefix /path/to/env --outname python_data  --config /path/to/config.yaml
```

This will generate two files `python_data.js` and `python_data.data` that you can use in the browser.
A sample config is located in [`tests/empack_test_config.yaml`](https://github.com/emscripten-forge/empack/blob/main/tests/empack_test_config.yaml)
