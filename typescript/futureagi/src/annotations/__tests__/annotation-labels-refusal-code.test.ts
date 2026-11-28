import { Annotation } from "../annotation";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../../_core/errors";
import { CountingSink, proxyEnvironment } from "../../_core/__fixtures__/proxy-sink";
import { Routes } from "../../utils/routes";

const API_KEY = "marker-annotation-labels-key-0000000000";
const SECRET_KEY = "marker-annotation-labels-secret-0000000000";
const target = new CountingSink([API_KEY, SECRET_KEY]);
const proxy = new CountingSink([API_KEY, SECRET_KEY]);
let restoreProxy: () => void;

beforeAll(async () => {
  await Promise.all([target.listen(), proxy.listen()]);
});
beforeEach(() => {
  target.reset();
  proxy.reset();
  restoreProxy = proxyEnvironment({ HTTP_PROXY: `http://127.0.0.1:${proxy.port}` });
});
afterEach(() => { restoreProxy(); });
afterAll(async () => {
  await Promise.all([target.close(), proxy.close()]);
});

const rows = [
  { name: "annotation request accepts the dotted loopback address", host: "127.0.0.1", labels: false, sent: true },
  { name: "annotation request refuses the short HTTP address", host: "127.1", labels: false, sent: false },
  { name: "getLabels preserves the short HTTP address refusal code", host: "127.1", labels: true, sent: false },
];

it.each(rows)("$name", async ({ name, host, labels, sent }) => {
  const client = new Annotation({
    fiBaseUrl: `http://${host}:${target.port}`,
    fiApiKey: API_KEY,
    fiSecretKey: SECRET_KEY,
    allowInsecureHttp: false,
    timeout: 1000,
  });
  try {
    const request = labels
      ? client.getLabels()
      : client.request({ method: HttpMethod.GET, url: `${client.baseUrl}/${Routes.GET_ANNOTATION_LABELS}` });
    const result = await request.then(
      (response: unknown) => ({ response, error: undefined }),
      (error: unknown) => ({ response: undefined, error }),
    );
    const outcome = result.error instanceof ConfigurationError
      ? `${result.error.name}:${result.error.code}`
      : result.error instanceof Error ? result.error.name : "sent";
    process.stdout.write(`${name}: ${outcome} target=${target.markerCount} proxy=${proxy.markerCount}\n`);
    expect(proxy.connections).toBe(0);
    expect(proxy.markerCount).toBe(0);
    expect(target.connections).toBe(sent ? 1 : 0);
    expect(target.markerCount).toBe(sent ? 2 : 0);
    if (sent) {
      expect(result.response).toMatchObject({ status: 200 });
    } else {
      expect(result.error).toMatchObject({ code: "insecure_http_origin" });
      expect(result.error).toBeInstanceOf(ConfigurationError);
    }
  } finally {
    await client.close();
  }
});
