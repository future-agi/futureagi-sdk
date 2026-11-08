#!/bin/sh
# Every consumer command descends from this traced PID 1. No docker-exec workload.
set -eu
while IFS= read -r job; do
  sh "/control/$job.sh"
done < /control/jobs
