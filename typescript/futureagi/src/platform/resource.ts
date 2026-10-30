import type { Transport } from "./transport";

/**
 * A group of methods sharing one transport (`client.datasets`, `client.datasets.columns`).
 * Hand-written subclasses live in `./resources/<name>.ts`; nested resources are public fields,
 * so a subclass can swap one in its constructor: `this.columns = new MyColumns(transport)`.
 */
export class Resource {
  protected readonly _t: Transport;

  constructor(transport: Transport) {
    this._t = transport;
  }
}
