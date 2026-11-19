import type { BaseClient } from "../../base-client.js";
import { ChatCompletions } from "./completions.js";

export class Chat {
  public readonly completions: ChatCompletions;

  constructor(client: BaseClient) {
    this.completions = new ChatCompletions(client);
  }
}

export { ChatCompletions };
