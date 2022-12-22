#!/bin/bash
set -e


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


# run in browser-main-thread backend 
# in a headless fashion
pyjs_code_runner run script \
    browser-main \
    --conda-env     /home/web_user/picomamba/env \
    --host-work-dir $SCRIPT_DIR/outdir/distribution \
    --mount         $SCRIPT_DIR/code:/home/web_user/code \
    --script        main_offline.py \
    --work-dir      /home/web_user/code \
    --port          8000 \
    --async-main    \
    --no-headless   \
    --slow-mo 10000