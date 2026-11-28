# Platform OpenAPI projection

`source.json` records two distinct digests. `source_digest` identifies the exact upstream OpenAPI bytes. `scoped.sha256` identifies the derived public document in `generated/`. The wrapper map's `contract_sha256` identifies the upstream input, not the wrapper map or the public document.

To rebuild from the upstream input, use `scripts/platform/build-platform-openapi.sh --input /path/to/contract.json`. The rebuild verifies the input against `source_digest`. The scope filter keeps admitted operations and their reachable components, then translates component names, operation IDs and SDK metadata into the public vocabulary. Paths, HTTP fields, protocol identifiers, discriminator tags and server error codes retain their wire spelling.

For a naming migration without the upstream input, use the `source.json`, `scope.json`, `wrapper-map.json` and `generated/futureagi-platform.openapi.json` from the same source tree. Put those files under `openapi/platform/` in a complete scratch checkout of the generator and its inputs. Run the following from the generator repository root:

```sh
node scripts/connectors/project_platform_scope.mjs "$scratch" --legacy-names \
  < "$scratch/openapi/platform/scope.json"
```

This mode verifies the existing **scoped** digest and requires the same operation scope. It updates the public document, scoped digest, operation inventory and the wrapper map's references for those operations without authenticating or replacing the upstream bytes. Omit `--legacy-names` for an input that uses the public names. Public-name reprojection can restrict the scope further; operations absent from the input require the upstream rebuild.

Run regeneration from the scratch checkout after the migration. The SDK script reads inputs from its own checkout; `--out` only changes where it writes artifacts. Generate the SDK and shared transport cases against the migrated inputs with:

```sh
(cd "$scratch" && scripts/generate-platform-sdk.sh && python3 scripts/platform/contract_cases.py)
```
