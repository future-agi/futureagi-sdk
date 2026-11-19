// Make a case repeatable: virtual clock, recorded timers, fixed randomness.
//
// Patched on globalThis only (never on a package path), so the same harness
// serves @agentcc/client 1.x and @future-agi/sdk/gateway.
//   setTimeout(fn, ms)    records ms, runs fn on the next macrotask, advances the clock
//   Date.now, performance.now   read the virtual clock
//   Math.random           a fixed sequence (mulberry32, reset per case)
//   crypto.randomUUID     counts up; crypto.getRandomValues fills from the sequence
//   AbortSignal.timeout   records ms; the signal never fires on its own (a scripted
//                         timeout rejects the fetch the way undici does instead)

export const EPOCH_MS = 1761177600000; // 2025-10-23T00:00:00Z

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class Determinism {
  constructor() {
    this.now = EPOCH_MS;
    this.timers = [];
    this.signalTimeouts = new WeakMap();
    this._saved = [];
    this._uuid = 0;
    this._random = mulberry32(1);
  }

  _patch(owner, name, value) {
    const desc = Object.getOwnPropertyDescriptor(owner, name);
    this._saved.push([owner, name, desc]);
    Object.defineProperty(owner, name, { value, configurable: true, writable: true, enumerable: desc ? desc.enumerable : false });
  }

  install() {
    const state = this;
    const realSetImmediate = globalThis.setImmediate;
    const realClearImmediate = globalThis.clearImmediate;
    const realTimeout = AbortSignal.timeout.bind(AbortSignal);
    this._patch(globalThis, "setTimeout", (fn, ms = 0, ...args) => {
      state.timers.push(Number(ms) || 0);
      state.now += Math.max(Number(ms) || 0, 0);
      return realSetImmediate(() => fn(...args));
    });
    this._patch(globalThis, "clearTimeout", (handle) => {
      if (handle) realClearImmediate(handle);
    });
    const RealDate = Date;
    class VirtualDate extends RealDate {
      constructor(...args) {
        if (args.length === 0) super(state.now);
        else super(...args);
      }
      static now() {
        return state.now;
      }
    }
    this._patch(globalThis, "Date", VirtualDate);
    this._patch(globalThis.performance, "now", () => state.now - EPOCH_MS);
    this._patch(Math, "random", () => state._random());
    if (globalThis.crypto) {
      this._patch(globalThis.crypto, "randomUUID", () => {
        state._uuid += 1;
        return `00000000-0000-4000-8000-${String(state._uuid).padStart(12, "0")}`;
      });
      this._patch(globalThis.crypto, "getRandomValues", (arr) => {
        for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(state._random() * 256);
        return arr;
      });
    }
    this._patch(AbortSignal, "timeout", (ms) => {
      const controller = new AbortController();
      state.signalTimeouts.set(controller.signal, ms);
      void realTimeout;
      return controller.signal;
    });
  }

  remove() {
    while (this._saved.length) {
      const [owner, name, desc] = this._saved.pop();
      if (desc) Object.defineProperty(owner, name, desc);
      else delete owner[name];
    }
  }

  report() {
    return this.timers.length ? { timers: this.timers } : {};
  }
}
