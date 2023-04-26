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
empack pack env --env-prefix /path/to/env
```

This will generate a few `.tag.gz` files that correspond to the packages in the environment located at `/path/to/env`.

You can also provide a custom config with the `--config` flag. A sample config is located in [`tests/empack_test_config.yaml`](https://github.com/emscripten-forge/empack/blob/main/tests/empack_test_config.yaml)


Run the following command for more information about the other CLI parameters:

```bash
empack pack env --help
```
