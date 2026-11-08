FROM debian:bookworm-slim
# Trusted observer only, built before any candidate is mounted or installed.
RUN apt-get update && apt-get install -y --no-install-recommends strace && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["strace"]
