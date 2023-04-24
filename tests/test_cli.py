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
            platform="emscripten-32",
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
