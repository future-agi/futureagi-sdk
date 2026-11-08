type Case = Record<string, any>;

export function envelopeAdapter(row: Case): boolean {
  return (row.envelope_adapter ?? ["prompts", "knowledgeBases", "scores"].includes(row.name.split(".")[0])) || row.adapter === "management";
}

export function payloads(row: Case): { wire: any; publicValue: any } {
  const explicit = row.invocation?.response;
  if (explicit) return { wire: explicit.wire, publicValue: explicit.public };
  if (row.success_status === 204) return { wire: undefined, publicValue: row.adapter === "management" ? undefined : null };
  const page: Record<string, any> = { count: 1, next: null, previous: null, results: [{ marker: "kept" }], total_pages: 1, current_page: 1 };
  if (row.adapter === "catalog") {
    const op = row.catalog;
    const put = (path: string, value: unknown) => {
      const parts = path.split(".");
      let at = page;
      for (const part of parts.slice(0, -1)) at = at[part] ??= {};
      at[parts[parts.length - 1]] = value;
    };
    if (op.pagination) {
      put(op.pagination.items, [{ marker: "kept" }]);
      if (op.pagination.total_items) put(op.pagination.total_items, 1);
    }
    return { wire: op.unwrap ? { [op.unwrap]: page } : page, publicValue: page };
  }
  if (envelopeAdapter(row)) {
    const wire = { status: true, result: page };
    return { wire, publicValue: (row.unwrap_result ?? row.name !== "scores.forSource") ? page : wire };
  }
  if (row.adapter === "core") {
    const wire = row.response_example ?? { status: true, result: page };
    return { wire, publicValue: wire };
  }
  const wire = structuredClone(row.response_example ?? page);
  return { wire, publicValue: row.public_response_field && wire && row.public_response_field in wire ? wire[row.public_response_field] : wire };
}
