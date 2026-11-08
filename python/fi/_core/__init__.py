"""The platform client core: shared by every platform namespace, private.

One module per concern, each 400 lines or fewer: ``errors`` (the status mapping and the transport
wording), ``policy`` (the generated operation table's shape and the four retry classes),
``request`` (paths, queries and bodies from an operation), ``idempotency``, ``origins`` (the
platform origin, its credential and the host guard), ``platform_base`` (the request executor),
``raw`` (``with_raw_response``), ``sse`` and ``resumable`` (streams), ``pagination`` (``Page``) and
``handles`` (``Deployment`` / ``Sandbox`` / ``Run`` share one base and one ``.wait()``).

Nothing here imports ``fi.utils``, ``fi.api`` or ``fi.experiments``, and ``import fi``
imports nothing here.
"""
