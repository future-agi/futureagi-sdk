import { publicValueAt } from "./contract-absence";

/** Assert real public absence for every retained Console-hidden scenario. */
export function assertConsoleAbsent(row: Record<string, any>, subject: { client: unknown; setupRequests: Request[]; handles: Record<string, any> }): void {
  expect(row.public_absence).toEqual({ py: ["client.agents", "client.environments"], ts: ["client.agents", "client.environments"] });
  expect(publicValueAt(subject.client, "client.agents")).toBeUndefined();
  expect(publicValueAt(subject.client, "client.environments")).toBeUndefined();
  expect(publicValueAt(subject.client, "client.agents.runs.get")).toBeUndefined();
  expect(publicValueAt(subject.client, "client.environments.list")).toBeUndefined();
  expect(subject.setupRequests).toEqual([]);
  expect(subject.handles).toEqual({});
}
