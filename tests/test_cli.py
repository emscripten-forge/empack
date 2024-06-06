import json

import pytest
from typer.testing import CliRunner

from empack.cli.main import app
from empack.micromamba_wrapper import create_environment

from .conftest import CHANNELS

runner = CliRunner()


class TestCLI:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.stdout

    @pytest.mark.parametrize("use_cache", [False, True])
    def test_pack_env(self, tmp_path, use_cache):
        prefix = tmp_path / "env"
        create_environment(
            prefix=prefix,
            packages=["numpy"],
            channels=CHANNELS,
            relocate_prefix="/",
            platform="emscripten-wasm32",
        )

        use_cache_arg = "--use-cache" if use_cache else "--no-use-cache"

        args = [
            "pack",
            "env",
            "--env-prefix",
            str(prefix),
            "--relocate-prefix",
            "/",
            "--outdir",
            str(tmp_path),
            use_cache_arg,
            "--compresslevel",
            "1",
        ]

        result = runner.invoke(app, args)
        assert result.exit_code == 0

        # create a directory with some files
        dir_name = "test_dir"
        dir_path = tmp_path / dir_name
        dir_path.mkdir()
        file1 = dir_path / "file1.txt"
        file1.write_text("file1")

        args = [
            "pack",
            "dir",
            "--host-dir",
            str(dir_path),
            "--mount-dir",
            "/",
            "--outname",
            "packaged_dir.tar.gz",
            "--outdir",
            str(tmp_path),
        ]
        result = runner.invoke(app, args)
        assert result.exit_code == 0

        # append the directory to the env
        args = [
            "pack",
            "append",
            "--env-meta",
            str(tmp_path),
            "--tarfile",
            str(tmp_path / "packaged_dir.tar.gz"),
        ]
        result = runner.invoke(app, args)
        print(result.stdout)
        assert result.exit_code == 0

        # check that there is a json with all the packages
        env_metadata_json_path = tmp_path / "empack_env_meta.json"
        assert env_metadata_json_path.exists()

        with open(env_metadata_json_path) as f:
            env_meta = json.load(f)
        packages = env_meta["packages"]
        env_meta_dict = dict()

        for pkg in packages:
            env_meta_dict[pkg["name"]] = pkg

        assert "packaged_dir.tar.gz" in env_meta_dict
        assert "numpy" in env_meta_dict
        assert "python" in env_meta_dict
