import assert from "node:assert/strict";
import { test } from "node:test";
import { createProvenanceVerifier, provenanceOccurrences, publicRemote } from "../hygiene-provenance.mjs";

const publicCommit = "a1".repeat(20);
const privateCommit = "b2".repeat(20);

test("only anonymous HTTPS public repository identities can be checked", () => {
  assert.equal(publicRemote("example/project"), "https://github.com/example/project.git");
  assert.equal(publicRemote("https://github.com/example/project.git"), "https://github.com/example/project.git");
  for (const value of ["file:///example", "http://127.0.0.1/project", "https://user:password@github.com/example/project", "git@github.com:example/project", "https://github.com/example/project?token=value"]) assert.equal(publicRemote(value), null);
});

test("proof fetches public refs only with no inherited credentials and does not fetch the candidate", () => {
  const commands = [];
  const verify = createProvenanceVerifier((command, args, options) => {
    assert.equal(command, "git");
    assert.equal(options.env.GIT_CONFIG_GLOBAL, "/dev/null");
    assert.equal(options.env.GIT_CONFIG_NOSYSTEM, "1");
    assert.equal(options.env.GIT_TERMINAL_PROMPT, "0");
    assert.equal(options.env.GIT_ALLOW_PROTOCOL, "https");
    assert.equal(options.env.GITHUB_TOKEN, undefined);
    assert.ok(args.includes("credential.helper="));
    commands.push(args);
    if (args.includes("ls-remote")) return `${publicCommit}\trefs/heads/main\n`;
    if (args.includes("rev-list")) return publicCommit + "\n";
    return "";
  });
  try {
    assert.equal(verify("example/project", publicCommit.slice(0, 10)), true);
    assert.equal(verify("example/project", privateCommit), false);
    assert.equal(commands.filter((args) => args.includes("ls-remote")).length, 1, "cache belongs only to this scan");
    const fetch = commands.find((args) => args.includes("fetch"));
    assert.ok(fetch.includes("refs/heads/main:refs/heads/main"));
    assert.ok(!fetch.includes(publicCommit) && !fetch.includes(privateCommit));
  } finally { verify.close(); }
});

test("unreachable, unavailable, ambiguous and private sources never receive clearance", () => {
  for (const mode of ["private", "missing", "ambiguous"]) {
    const verify = createProvenanceVerifier((_command, args) => {
      if (mode === "private") throw new Error("anonymous access refused");
      if (args.includes("ls-remote")) return `${publicCommit}\trefs/heads/main\n`;
      if (args.includes("rev-list")) return mode === "missing" ? privateCommit : `${publicCommit}\n${publicCommit.slice(0, 10)}${"c3".repeat(15)}`;
      return "";
    });
    try { assert.equal(verify("example/project", publicCommit.slice(0, 10)), false, mode); }
    finally { verify.close(); }
  }
});

test("top-level provenance does not certify a nested object or a matching prose occurrence", () => {
  const text = JSON.stringify({ source: "example/project", revision: publicCommit, prose: publicCommit, nested: { revision: publicCommit } });
  const occurrences = provenanceOccurrences("source.json", text, () => true);
  assert.deepEqual([...occurrences], [text.indexOf(publicCommit)]);
  assert.equal(provenanceOccurrences("source.py", text, () => true).size, 0);
});
