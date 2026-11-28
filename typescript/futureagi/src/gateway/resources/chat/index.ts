import type { BaseClient } from "../../base-client";
import { ChatCompletions } from "./completions";

export class Chat {
  public readonly completions: ChatCompletions;

  constructor(client: BaseClient) {
    this.completions = new ChatCompletions(client);
  }
}

export { ChatCompletions };
