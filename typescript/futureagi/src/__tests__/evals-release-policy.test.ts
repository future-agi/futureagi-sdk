import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { transpileModule, ScriptTarget } from "typescript";

const packageDir = resolve(__dirname, "../..");
const read = (file: string) => readFileSync(resolve(packageDir, file), "utf8");

describe("evaluation release policy", () => {
  it("keeps the template-runner subpath and type entries unregistered", () => {
    const manifest = JSON.parse(read("package.json"));
    expect(Object.keys(manifest.exports).filter((key) => key.startsWith("./evals"))).toEqual([]);
    for (const mapping of Object.values(manifest.typesVersions ?? {})) {
      expect(Object.keys(mapping as object).filter((key) => key.startsWith("evals"))).toEqual([]);
    }
    // Exclude the deferred top-level runner, not the shipped platform resource.
    for (const output of ["esm", "src", "esnext"]) {
      expect(manifest.files).toEqual(expect.arrayContaining([
        `!dist/${output}/evals/**`, `!dist/${output}/evals.*`,
      ]));
    }
    expect(manifest.files).not.toContain("!dist/**/evals/**");
    expect(manifest.files).not.toContain("!dist/**/evals.*");
  });

  it("has no retired evaluation dependency in either workspace or any lockfile", () => {
    for (const file of ["package.json", "../package.json", "package-lock.json", "pnpm-lock.yaml", "../pnpm-lock.yaml"]) {
      expect(read(file)).not.toContain("@future-agi/ai-evaluation");
    }
  });

  it("does not advertise the disabled import or retired install", () => {
    expect(read("README.md")).not.toContain("@future-agi/sdk/evals");
    expect(read("README.md")).not.toContain("@future-agi/ai-evaluation");
  });
});

describe("documented deterministic REST example", () => {
  const environment = { env: {
    FI_BASE_URL: "http://127.0.0.1:9019", FI_API_KEY: "personal-fixture", FI_SECRET_KEY: "personal-fixture-secret",
  } };
  function example(fetch: unknown, process: unknown = environment): Promise<unknown> {
    const readme = read("README.md");
    const section = readme.split("### Run a deterministic evaluation over REST\n")[1];
    const snippet = section?.match(/```ts\n([\s\S]*?)```/)?.[1];
    expect(snippet).toBeDefined();
    const javascript = transpileModule(snippet!, { compilerOptions: { target: ScriptTarget.ES2020 } }).outputText;
    return new Function("fetch", "process", `${javascript}\nreturn evaluateJson();`)(fetch, process);
  }

  it("uses personal credentials and the pinned scalar-input REST contract", async () => {
    const result = [{ evaluations: [{ name: "is_json", output: true, runtime: 0 }] }];
    const transport = jest.fn(async (url: URL, init: RequestInit) => {
      expect(url.href).toBe("http://127.0.0.1:9019/sdk/api/v1/new-eval/");
      expect(init.method).toBe("POST");
      expect(init.redirect).toBe("error");
      expect(init.headers).toMatchObject({ "X-Api-Key": "personal-fixture", "X-Secret-Key": "personal-fixture-secret" });
      expect(JSON.parse(init.body as string)).toEqual({ eval_name: "is_json", inputs: { output: '{"answer":42}' }, is_async: false });
      return new Response(JSON.stringify({ status: true, result }));
    });
    await expect(example(transport)).resolves.toEqual(result);
    expect(transport).toHaveBeenCalledTimes(1);
  });

  it.each([400, 401, 403, 500])("does not treat HTTP %i as a successful score", async (status) => {
    const transport = jest.fn(async () => new Response(JSON.stringify({ status: false }), { status }));
    await expect(example(transport)).rejects.toThrow(`Evaluation failed (HTTP ${status})`);
    expect(transport).toHaveBeenCalledTimes(1);
  });

  it("rejects a failed envelope even on HTTP 200", async () => {
    await expect(example(async () => new Response(JSON.stringify({ status: false }))))
      .rejects.toThrow("Evaluation failed (HTTP 200)");
  });

  it("never calls fetch without explicit personal credentials", async () => {
    const transport = jest.fn();
    await expect(example(transport, { env: {} })).rejects.toThrow("Set FI_BASE_URL, FI_API_KEY and FI_SECRET_KEY");
    expect(transport).not.toHaveBeenCalled();
  });
});
