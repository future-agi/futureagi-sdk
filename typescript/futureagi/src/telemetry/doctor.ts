#!/usr/bin/env node
import { doctorText } from "./status";

if (process.argv[2] === "doctor") console.log(doctorText());
else {
  console.error("Usage: futureagi-telemetry doctor");
  process.exitCode = 2;
}
