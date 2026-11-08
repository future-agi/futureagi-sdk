"""An embedded CLI invocation must not reconfigure its caller's SDK logging."""

import argparse
import logging

import pytest

from fi._cli import main as cli
from fi._cli import registry


@pytest.mark.parametrize("outcome", [0, 3, "interrupt", "unexpected"])
@pytest.mark.parametrize("verbose,quiet", [(False, False), (True, False), (False, True)])
def test_cli_restores_logging_on_every_exit(monkeypatch, capsys, outcome, verbose, quiet):
    logger = logging.getLogger("fi")
    old_level, old_handlers = logger.level, logger.handlers[:]
    caller_handler = logging.NullHandler()
    logger.addHandler(caller_handler)
    logger.setLevel(logging.ERROR)
    before_handlers = logger.handlers[:]

    def command(args):
        expected = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
        assert logger.level == expected
        logging.getLogger("fi.gateway").warning("during command")
        if outcome == "interrupt":
            raise KeyboardInterrupt()
        if outcome == "unexpected":
            raise RuntimeError("unexpected command failure")
        return outcome

    parser = argparse.ArgumentParser()
    parser.set_defaults(command="stub", func=command, verbose=verbose, quiet=quiet)
    monkeypatch.setattr(cli, "build_parser", lambda: parser)
    monkeypatch.setattr(registry, "run_pre_parse", lambda argv: None)
    try:
        if outcome == "unexpected":
            with pytest.raises(RuntimeError, match="unexpected command failure"):
                cli.main([])
        else:
            assert cli.main([]) == (4 if outcome == "interrupt" else outcome)
        assert "during command" in capsys.readouterr().err
        assert logger.level == logging.ERROR
        assert logger.handlers == before_handlers
    finally:
        logger.setLevel(old_level)
        for handler in logger.handlers[:]:
            if handler not in old_handlers:
                logger.removeHandler(handler)
                handler.close()
