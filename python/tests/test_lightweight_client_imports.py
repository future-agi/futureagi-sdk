"""Client imports stay lightweight without changing shared dataset types."""

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


_SOURCE = Path(__file__).resolve().parents[1]


def _run_isolated(code, tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    bootstrap = """
import sys

def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise AssertionError("Network access is not allowed in this test")

sys.addaudithook(deny_network)
"""
    result = subprocess.run(
        [
            sys.executable, "-I", "-B", "-c",
            f"import sys; sys.path.insert(0, {str(_SOURCE)!r})\n"
            + textwrap.dedent(bootstrap) + textwrap.dedent(code),
        ],
        cwd=tmp_path,
        env={"PATH": os.defpath, "HOME": str(home), "TMPDIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("statement", [
    "import fi",
    "from fi.prompt import Prompt",
    "from fi.kb import KnowledgeBase",
    "import fi.prompt, fi.kb",
])
def test_client_import_does_not_load_dataframe_stack(statement, tmp_path):
    _run_isolated(
        f"""
{statement}
loaded = sorted(name for name in sys.modules
                if name.split('.')[0] in {{'numpy', 'pandas'}})
assert not loaded, 'Unexpected dataframe imports: ' + ', '.join(loaded)
""",
        tmp_path,
    )


@pytest.mark.parametrize("first_import", ["fi.utils.errors", "fi.utils.types"])
def test_shared_enums_keep_identity_annotations_and_pickle_path(first_import, tmp_path):
    _run_isolated(
        f"import {first_import}\n" + textwrap.dedent("""
        import pickle
        from typing import Union, get_type_hints
        from fi.api.auth import DatasetNotFoundError, MissingAuthError
        from fi._credentials import MissingAuthError as CredentialsMissingAuthError
        from fi.utils import errors, types

        assert DatasetNotFoundError is errors.DatasetNotFoundError
        assert MissingAuthError is errors.MissingAuthError is CredentialsMissingAuthError
        assert errors.ModelTypes is types.ModelTypes
        assert errors.Environments is types.Environments
        assert [(member.name, member.value) for member in types.ModelTypes] == [
            ('GENERATIVE_LLM', 'GenerativeLLM'),
            ('GENERATIVE_IMAGE', 'GenerativeImage'),
        ]
        assert types.ModelTypes.get_choices() == [
            ('GenerativeLLM', 'Generative Llm'),
            ('GenerativeImage', 'Generative Image'),
        ]
        assert [(member.name, member.value) for member in types.Environments] == [
            ('TRAINING', 1), ('VALIDATION', 2), ('PRODUCTION', 3), ('CORPUS', 4),
        ]
        assert get_type_hints(errors.InvalidSupportedType.__init__)['value'] == Union[
            types.ModelTypes, types.Environments
        ]
        for enum in (types.ModelTypes, types.Environments):
            assert enum.__module__ == 'fi.utils.types'
            assert pickle.loads(pickle.dumps(enum)) is enum
            for member in enum:
                assert enum(member.value) is member
                for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
                    assert pickle.loads(pickle.dumps(member, protocol=protocol)) is member
                err = errors.InvalidSupportedType('kind', member, 'supported values')
                assert err.value is member
                assert err.get_error_code() == 'UNSUPPORTED_TYPE_OR_VALUE'
                assert err.get_message() == (
                    f'kind with value {member!r} is not supported as of now. '
                    'Supported types/values are: supported values.'
                )
        # Protocol-0 values written using the historical public module path.
        assert pickle.loads(
            b'cfi.utils.types\\nEnvironments\\n(I3\\ntR.'
        ) is types.Environments.PRODUCTION
        assert pickle.loads(
            b'cfi.utils.types\\nModelTypes\\n(VGenerativeLLM\\ntR.'
        ) is types.ModelTypes.GENERATIVE_LLM
        """),
        tmp_path,
    )


@pytest.mark.parametrize("container", ["list", "numpy", "pandas"])
def test_embedding_validation_keeps_supported_containers(container):
    import numpy as np
    import pandas as pd
    from fi.utils.types import Embedding

    make = {"list": list, "numpy": np.array, "pandas": pd.Series}[container]
    embedding = Embedding(
        vector=make([0.25, 0.75]), data=make(["first", "second"]),
        link_to_data="https://example.invalid/embedding",
    )
    assert embedding.validate("feature") is None
    with pytest.raises(ValueError, match="size of 1"):
        Embedding(vector=make([1.0])).validate("feature")
    with pytest.raises(TypeError, match="integers and/or floats"):
        Embedding(vector=make(["first", "second"])).validate("feature")
    with pytest.raises(TypeError, match="must contain strings"):
        Embedding(vector=[1.0, 2.0], data=make([1, 2])).validate("feature")


def test_embedding_validation_keeps_numpy_scalars_and_type_hints():
    import numpy as np
    import pandas as pd
    from typing import List, Union, get_type_hints
    from fi.utils.types import Embedding

    assert Embedding(vector=[np.int16(1), np.int32(2), np.float16(0.5), np.float32(0.75)]).validate("feature") is None
    assert not Embedding._is_valid_iterable((1.0, 2.0))
    assert get_type_hints(Embedding._is_valid_iterable)["data"] == Union[
        str, List[str], List[float], np.ndarray, pd.Series
    ]
