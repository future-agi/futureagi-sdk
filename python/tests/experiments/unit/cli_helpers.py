import contextlib
import io

from fi._cli.main import main


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def write_rows(path, rows):
    import json

    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return str(path)
