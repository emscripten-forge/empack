import textwrap

import pytest
from pyjs_code_runner.run import run

from empack.micromamba_wrapper import create_environment

from .conftest import CHANNELS

PYJS_VERSION = "2.1.0"
PYJS_SPEC = f"pyjs>={PYJS_VERSION}"


@pytest.mark.parametrize("backend_type", ["browser-main", "browser-worker"])
def test_integration(tmp_path, tmp_path_module, free_port, backend_type):
    packages = ["numpy", "scipy"]
    packages += [PYJS_SPEC]

    prefix = tmp_path / "env"
    create_environment(
        prefix=prefix,
        packages=packages,
        channels=CHANNELS,
        relocate_prefix="/",
        platform="emscripten-wasm32",
    )

    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    script_path = script_dir / "main.py"

    py_main = """
import scipy
import numpy as np
print(np.__version__)
print(scipy.__version__)
from scipy.linalg import lapack
print(lapack.dlamch("Epsilon-Machine"))
    """

    with open(script_path, "w") as f:
        f.write(textwrap.dedent(py_main))

    run(
        conda_env=prefix,
        relocate_prefix="/",
        backend_type=backend_type,
        script="main.py",
        async_main=False,
        mounts=[(script_dir, "/tests")],
        work_dir="/tests",
        use_cache=True,
        cache_dir=tmp_path_module,
        backend_kwargs=dict(port=free_port, slow_mo=0, headless=True),
    )
