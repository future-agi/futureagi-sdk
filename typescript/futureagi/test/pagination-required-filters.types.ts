// FA model_hub/views/prompt_labels.py:382-402 accepts either template selector.
import type { ModelHubPromptLabelsTemplateLabelsData } from "../src/generated/openapi/types.gen.js";

type Query = NonNullable<ModelHubPromptLabelsTemplateLabelsData["query"]>;
const byId: Query = { template_id: "template-id" };
const byName: Query = { template_name: "template-name" };
// @ts-expect-error The endpoint does not support framework-added pagination.
const unsupportedPage: Query = { page: 1 };
void [byId, byName, unsupportedPage];
