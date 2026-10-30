const warned = new Set<string>();

/** Warn once per operation when a beta or deprecated method is called. */
export function warnStability(opId: string, stability: string): void {
  if (warned.has(opId)) {
    return;
  }
  warned.add(opId);
  if (stability === "beta") {
    console.warn(`[futureagi] ${opId} is in beta and may change without notice.`);
  } else if (stability === "deprecated") {
    console.warn(`[futureagi] ${opId} is deprecated.`);
  }
}

/** Test hook: forget which operations have warned. */
export function resetStabilityWarnings(): void {
  warned.clear();
}
