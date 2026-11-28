"""The sandbox channel: exec streams over one WebSocket (``fi.sandbox`` uses it for
``commands.exec_stream``, and the command line for ``rsh``, ``ssh``, ``rsync`` and ``scp``).

``constants`` holds every wire value (the channel contract's), ``protocol`` the frame codec and the
credit-counting state of one stream, ``connect`` how a mint reply becomes a connection, and
``_async`` / ``_sync`` the two stream handles (written separately: each rides its own
``websockets`` client)."""
