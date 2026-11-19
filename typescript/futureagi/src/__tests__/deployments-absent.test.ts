import * as root from "../index";
import { FutureAGIClient } from "../index";

test("disabled deployments have no root export, accessor or declared type", () => {
  const fetchMock = jest.fn(() => {
    throw new Error("Absence checks must not send a request");
  });
  const client = new FutureAGIClient({
    baseUrl: "http://127.0.0.1:9",
    fetch: fetchMock as typeof fetch,
  });
  for (const target of [client, client.withOptions({ retries: 0 })]) {
    expect("deployments" in target).toBe(false);
    // @ts-expect-error Disabled namespaces must not appear in declarations.
    expect(target.deployments).toBeUndefined();
  }
  for (const name of ["Deployment", "Deployments", "DeploymentsClient", "deployments"]) {
    expect(Object.prototype.hasOwnProperty.call(root, name)).toBe(false);
  }
  // @ts-expect-error Disabled handles must not be exported from the root.
  expect(root.Deployment).toBeUndefined();
  expect(fetchMock).not.toHaveBeenCalled();
});
