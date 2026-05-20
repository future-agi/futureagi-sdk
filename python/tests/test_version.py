from importlib.metadata import version

import fi


def test_public_version_matches_package_metadata():
    assert fi.__version__ == version("futureagi")
