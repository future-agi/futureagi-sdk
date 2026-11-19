/** Base identity shared by status, connection and body-read errors. */
export class AgentCCError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AgentCCError";
  }
}
