"""Content-free tracing diagnostics: python -m fi.telemetry doctor."""
import argparse

from ._status import status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor"])
    parser.parse_args()
    facts = status()
    # Do not print arbitrary span/resource values, skill names, or exception
    # messages: applications may accidentally put credentials in those fields.
    for key in ("otel_found", "provider", "processor_installed", "mode", "truth_table_row", "agent_name_source", "rule"):
        print(f"{key}: {facts[key]}")
    print(f'last_load: {"recorded" if facts["last_load"] else "none"}')
    if facts["mode"] == "off":
        print('Enable: fi.telemetry.configure(skills_tracing="on")')
    elif not facts["otel_found"]:
        print('Install futureagi[otel] and configure an application-owned tracer provider.')
    elif facts["provider"] == "none":
        print('Pass your provider to fi.telemetry.configure(tracer_provider=provider).')
    if facts["agent_name_source"] == "none":
        print('Name your agent with agent_scope(agent="your-agent") or OTEL_SERVICE_NAME.')


if __name__ == "__main__":
    main()
