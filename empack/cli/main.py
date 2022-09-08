from .app import app
from .pack import *  # noqa: F401, F403
from .repodata import *  # noqa: F401, F403
from .version import *  # noqa: F401, F403

if __name__ == "__main__":
    app()
