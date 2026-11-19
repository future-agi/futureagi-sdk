// Contract r3 additions, sha256 11178e87768b2e5ff6df3b663832795facfc73b89f7083afdfb3e006a07d7c78.
import type { ContractRow } from "./onekey-contract-fixtures.js";
export const CONTRACT_R3_ROWS: ContractRow[] = [
  {
    "status": 410,
    "code": "model_expired",
    "type": "not_found",
    "remedy": "Choose an active replacement model; an expired or shut-down model is not restored by retrying.",
    "retry": "never",
    "name": "APIStatusError",
    "category": "generic",
    "metadata": {
      "reason": "example"
    }
  },
  {
    "status": 404,
    "code": "no_provider_matches",
    "type": "not_found",
    "remedy": "Adjust the request provider filters/order/allow_fallbacks to include an eligible endpoint; do not bypass organization policy.",
    "retry": "never",
    "name": "NotFoundError",
    "category": "generic",
    "metadata": {
      "reason": "example"
    }
  },
  {
    "status": 400,
    "code": "provider_preference_unavailable",
    "type": "invalid_request_error",
    "remedy": "Remove/change the unsupported provider preference, or choose a model whose endpoint information supports it.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": {
      "reason": "example"
    }
  },
  {
    "status": 400,
    "code": "model_ambiguous",
    "type": "invalid_request_error",
    "remedy": "Send one of the complete catalog model IDs named by the refusal instead of an ambiguous bare name.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "no_auto_candidate",
    "type": "invalid_request_error",
    "remedy": "Choose an eligible explicit model or correct the auto candidate/capability/price constraints; if there are no usable routes, enable credits or add an own-provider route through authorized controls.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "omega_default_unroutable",
    "type": "invalid_request_error",
    "remedy": "Enable managed models through the authorized credits control or add an own provider; alternatively configure a routable default model.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": {
      "remedy_hint": "example",
      "model_alias_requested": "example"
    }
  },
  {
    "status": 400,
    "code": "route_hint_unsupported",
    "type": "invalid_request_error",
    "remedy": "For model auto, use route-hint cost, balanced or quality, or omit the hint; latency ranking is unsupported.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "routing_field_not_yet_supported",
    "type": "invalid_request_error",
    "remedy": "Remove the unimplemented field or use a routing field the gateway supports.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "invalid_provider_preference",
    "type": "invalid_request_error",
    "remedy": "Correct or remove the field named by error.param; use a supported provider preference with its documented type and allowed values.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "invalid_routing_field",
    "type": "invalid_request_error",
    "remedy": "Correct or remove the field named by error.param. Do not send models and fallbacks together; obey the model-list and fallback-list limits and required shapes.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "extra_body_conflict",
    "type": "invalid_request_error",
    "remedy": "Remove the conflicting duplicate or make it agree with the top-level field. Send pre-read model, messages, streaming, user, metadata and session fields at the top level.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 400,
    "code": "invalid_extra_body",
    "type": "invalid_request_error",
    "remedy": "Send extra_body as a non-nested JSON object whose fields have the request types the gateway expects, or remove it.",
    "retry": "never",
    "name": "BadRequestError",
    "category": "generic",
    "metadata": null
  },
  {
    "status": 404,
    "code": "provider_not_found",
    "type": "not_found",
    "remedy": "Correct or remove the provider lock, or ask an authorized operator to configure the intended provider; do not bypass provider access policy.",
    "retry": "never",
    "name": "NotFoundError",
    "category": "generic",
    "metadata": null
  }
];
