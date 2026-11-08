/**
 * Credentials for one call, by mode, from the run's fixtures file (secrets; never in evidence).
 *
 *   none        no credential at all
 *   ee-key      self-host: an EE account key from /auth/keys, `Authorization: Bearer`, plus the
 *               org and workspace selectors EE reads (`x-omega-org`, `x-omega-workspace`)
 *   fa-session  through the gateway with a Future AGI browser session token (NOT an SDK
 *               credential), with `x-organization-id`/`x-workspace-id`
 *   fi-keypair  through the gateway with the FI key pair (`X-Api-Key`, `X-Secret-Key`); a run whose
 *               fixtures hold no FI key pair skips these cases
 *
 * `scopeOrg` (a case's tenant.scopeOrg) sends `org`'s credential with the OTHER org's scope selectors:
 * the forged-selector attack. For fi-keypair the scope org's x-organization-id/x-workspace-id are sent
 * when the fixtures name them (skipped otherwise).
 *
 * Returns { headers } or { skip: reason } when the fixtures hold no such credential.
 */

export const MODES = Object.freeze(["none", "ee-key", "fa-session", "fi-keypair"]);

export function credentialFor(fixtures, mode, org, role, { omitScopeHeaders = false, scopeOrg } = {}) {
  if (mode === "none" || role === "anonymous") return { headers: {} };
  if (mode === "ee-key") {
    const tenant = fixtures?.ee?.[org];
    const key = tenant?.keys?.[role];
    if (!tenant || !key) return { skip: `no EE ${role} key for org ${org}` };
    const scope = fixtures.ee[scopeOrg ?? org];
    if (!scope) return { skip: `no EE scope ids for org ${scopeOrg}` };
    return {
      headers: {
        authorization: `Bearer ${key}`,
        ...(omitScopeHeaders ? {} : { "x-omega-org": scope.orgId, "x-omega-workspace": scope.workspaceId }),
      },
    };
  }
  if (mode === "fa-session") {
    const tenant = fixtures?.fa?.[org];
    const token = tenant?.tokens?.[role];
    if (!tenant || !token) return { skip: `no Future AGI ${role} session for org ${org}` };
    const scope = fixtures.fa[scopeOrg ?? org];
    if (!scope) return { skip: `no Future AGI scope ids for org ${scopeOrg}` };
    return {
      headers: {
        authorization: `Bearer ${token}`,
        ...(omitScopeHeaders ? {} : { "x-organization-id": scope.organizationId, "x-workspace-id": scope.workspaceId }),
      },
    };
  }
  if (mode === "fi-keypair") {
    const pair = fixtures?.fi?.[org]?.keys?.[role];
    if (!pair) return { skip: `no FI key pair for org ${org} ${role} (the fixtures hold none)` };
    const headers = { "x-api-key": pair.apiKey, "x-secret-key": pair.secretKey };
    if (!scopeOrg) return { headers };
    const scope = fixtures.fi?.[scopeOrg];
    if (!scope?.workspaceId) return { skip: `no FI scope ids for org ${scopeOrg} (the fixtures hold none)` };
    return { headers: { ...headers, "x-workspace-id": scope.workspaceId, ...(scope.organizationId ? { "x-organization-id": scope.organizationId } : {}) } };
  }
  throw new Error(`unknown mode ${mode}`);
}

/** Every credential value in the fixtures, so a receipt can be scanned for them before it is written. */
export function secretValues(fixtures) {
  const out = [];
  const walk = (node, key) => {
    if (typeof node === "string" && /key|token|secret|password/i.test(key ?? "") && node.length >= 8) out.push(node);
    else if (node && typeof node === "object") for (const [k, v] of Object.entries(node)) walk(v, /^(keys|tokens)$/.test(key ?? "") ? `${key}.${k}` : k);
  };
  walk(fixtures, "");
  return out;
}
