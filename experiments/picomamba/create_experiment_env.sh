#!/bin/bash
set -e

if true; then
    micromamba create \
        --prefix /home/web_user/picomamba/env \
        --platform=emscripten-32 \
        -c https://repo.mamba.pm/emscripten-forge \
        -c https://repo.mamba.pm/conda-forge \
        --yes \
        python numpy pytest nlohmann_json pyjs libsolv pybind11
fi