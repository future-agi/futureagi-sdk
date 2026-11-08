"""The managed-run CLI. Only argparse is imported while command groups load."""
import argparse


def _data(value):
    import json

    try:
        parsed = json.loads(value)
    except ValueError:
        raise argparse.ArgumentTypeError("--data must be a JSON object") from None
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("--data must be a JSON object")
    return parsed


def register(subparsers):
    """Add runs beneath agents, preserving a previously registered agents group."""
    from fi._cli.registry import set_section

    agents = subparsers.choices.get("agents")
    if agents is None:
        agents = subparsers.add_parser("agents", help="Managed agents")
    groups = next(
        (a for a in agents._actions if isinstance(a, argparse._SubParsersAction)), None
    )
    if groups is None:
        groups = agents.add_subparsers(dest="agent_command", required=True)
    root = groups.add_parser("runs", help="Run conversations and read their evidence")
    actions = root.add_subparsers(dest="run_command", required=True)
    names = (
        "create",
        "list",
        "get",
        "delete",
        "events",
        "send",
        "cancel",
        "interrupt",
        "resume",
        "retry",
        "fork",
        "tree",
        "observations",
        "evidence",
        "proof-pack",
        "control-status",
        "approvals",
        "list-approvals",
        "rating-get",
        "rating-set",
        "ratings-summary",
        "ratings-trajectory",
        "wait",
        "wait-for-approval",
    )
    for name in names:
        command = actions.add_parser(name)
        if name not in (
            "create",
            "list",
            "list-approvals",
            "ratings-summary",
            "ratings-trajectory",
        ):
            command.add_argument("run_id")
        command.add_argument(
            "--json",
            action="store_true",
            help="Print machine-readable JSON (the default)",
        )
        command.add_argument(
            "--data",
            type=_data,
            default={},
            help="SDK keyword arguments as JSON, using snake_case keys",
        )
        if name in ("create", "send"):
            command.add_argument("--input", required=True)
        if name in ("create", "send", "resume", "retry", "fork"):
            command.add_argument("--idempotency-key")
        if name == "create":
            command.add_argument("--wait", action="store_true")
        if name in ("create", "wait", "wait-for-approval"):
            command.add_argument(
                "--timeout", type=float, default=300.0, help="Wait timeout in seconds"
            )
        if name == "events":
            command.add_argument(
                "--after", help="Durable event sequence to resume strictly after"
            )
        command.set_defaults(func=execute)
    set_section("agents", "platform")


def execute(args):
    """Dispatch exclusively through the public SDK and serialize each stream event as one line."""
    import inspect
    import json
    from contextlib import closing
    from fi import FutureAGIClient
    from fi.errors import ConfigurationError

    def emit(value):
        if hasattr(value, "to_dict"):
            value = value.to_dict()
        elif hasattr(value, "raw"):
            value = value.raw
        print(json.dumps(value, ensure_ascii=True))

    with FutureAGIClient() as client:
        name, options = args.run_command.replace("-", "_"), dict(args.data)
        runs = client.agents.runs
        if name in ("ratings_summary", "ratings_trajectory"):
            target = getattr(client.agents.ratings, name.removeprefix("ratings_"))
        elif name in ("create", "list", "list_approvals"):
            target = getattr(runs, name)
        elif name in ("get", "delete"):
            target = getattr(runs, name)
            options["run_id"] = args.run_id
        else:
            run = runs.get(args.run_id)
            target = (
                getattr(run.rating, name.removeprefix("rating_"))
                if name.startswith("rating_")
                else getattr(run, name)
            )
        for key in ("input", "idempotency_key", "wait", "timeout", "after"):
            if hasattr(args, key) and getattr(args, key) is not None:
                options[key] = getattr(args, key)
        try:
            inspect.signature(target).bind(**options)
        except TypeError as exc:
            raise ConfigurationError(str(exc), code="invalid_arguments") from None
        result = target(**options)
        if name == "events":
            with closing(result):
                for event in result:
                    emit(event)
        else:
            emit(result)
    return 0
