#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
OUTDIR=$SCRIPT_DIR/outdir
EMPACK_CONFIG_URL="https://raw.githubusercontent.com/emscripten-forge/recipes/main/empack_config.yaml"
EMPACK_CONFIG=$OUTDIR/empack_config.yaml
DISTRIBUTION_DIR=$OUTDIR/distribution
EMSCRIPTEN_32_ENV_PREFIX=/home/web_user/picomamba/env

DIST_VERSION="v2"
PYJS_VERSION=0.16.0

mkdir -p $DISTRIBUTION_DIR

########################################################
# shrink repodata
########################################################
if false; then
    echo "shrink repodata"
    empack repodata shrink --outdir $OUTDIR
    cp $OUTDIR/arch_repodata_picomamba.tar.bz2          $DISTRIBUTION_DIR/arch_repodata_picomamba_$DIST_VERSION.tar.bz2
    cp $OUTDIR/noarch_repodata_picomamba.tar.bz2        $DISTRIBUTION_DIR/noarch_repodata_picomamba_$DIST_VERSION.tar.bz2     
fi

########################################################
# package repodata
########################################################
if true; then
    echo "download wget"
    wget $EMPACK_CONFIG_URL -O $EMPACK_CONFIG
fi


########################################################
# package repodata
########################################################
if true; then
    echo "pack repodata wget"
    empack pack repodata \
        --repodata $OUTDIR/arch_repodata.json \
        --env-prefix $EMSCRIPTEN_32_ENV_PREFIX \
        --config $EMPACK_CONFIG \
        --export-name "globalThis.EmscriptenForgeModule" \
        --channel https://repo.mamba.pm/emscripten-forge \
        --channel https://repo.mamba.pm/conda-forge \
        --outdir $DISTRIBUTION_DIR\

fi

########################################################
# get pyjs
########################################################
if true; then
    echo "get pyjs driver"
    if [ -d "$EMSCRIPTEN_32_ENV_PREFIX" ]; then rm -Rf $EMSCRIPTEN_32_ENV_PREFIX; fi
    micromamba create --prefix $EMSCRIPTEN_32_ENV_PREFIX --platform=emscripten-32 "pyjs>=0.16" --yes
    cp $EMSCRIPTEN_32_ENV_PREFIX/lib_js/pyjs/pyjs_runtime_browser.js   $DISTRIBUTION_DIR/pyjs_runtime_browser_$PYJS_VERSION.js
    cp $EMSCRIPTEN_32_ENV_PREFIX/lib_js/pyjs/pyjs_runtime_browser.wasm $DISTRIBUTION_DIR/pyjs_runtime_browser_$PYJS_VERSION.wasm

    sed -i 's/pyjs_runtime_browser.wasm/pyjs_runtime_browser_$PYJS_VERSION.wasm/' $DISTRIBUTION_DIR/pyjs_runtime_browser_$PYJS_VERSION.js

    if [ -d "$EMSCRIPTEN_32_ENV_PREFIX" ]; then rm -Rf $EMSCRIPTEN_32_ENV_PREFIX; fi

fi 


