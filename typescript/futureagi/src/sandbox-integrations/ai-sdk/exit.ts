/**
 * One shell exit code for how a sandbox command ended. It is the table of `exit_status` in
 * python/fi/sandbox/types.py, which the `sandbox exec` command and the Python integrations use, so a model sees the
 * same codes from every Future AGI surface (and the codes E2B and GNU `timeout` use):
 *
 * | How it ended                         | Exit code      | Note appended to stderr                        |
 * |--------------------------------------|----------------|------------------------------------------------|
 * | cancelled                            | 130            | `Command was cancelled`                        |
 * | timed out                            | 124            | `Command timed out after {t} seconds`          |
 * | could not start (`error`)            | 1              | `The command could not start: {error}`         |
 * | its own exit code                    | that code      | -                                              |
 * | a signal with a Linux number N       | 128 + N        | `Command was ended by signal {signal}`         |
 * | anything else                        | 1              | `Command ended without an exit code ({signal})` |
 *
 * A cancel wins over a timeout, and both over the signal that carried them out. Signal numbers are Linux's: the
 * sandbox runs Linux, whatever the calling computer numbers them.
 */

/** The command could not start, or it ended in a way no other code describes. */
export const EXIT_FAILED = 1;
/** The command ran past its time limit and was stopped. */
export const EXIT_TIMED_OUT = 124;
/** A signal ended the command: this plus the signal's Linux number. */
export const EXIT_SIGNAL_BASE = 128;
/** The command was cancelled (an abort, or `commands.cancel`). */
export const EXIT_CANCELLED = 130;

/** Signal numbers on Linux, where sandboxes run (the same table as python/fi/sandbox/types.py). */
export const LINUX_SIGNALS: Readonly<Record<string, number>> = Object.freeze({
  SIGHUP: 1,
  SIGINT: 2,
  SIGQUIT: 3,
  SIGILL: 4,
  SIGTRAP: 5,
  SIGABRT: 6,
  SIGIOT: 6,
  SIGBUS: 7,
  SIGFPE: 8,
  SIGKILL: 9,
  SIGUSR1: 10,
  SIGSEGV: 11,
  SIGUSR2: 12,
  SIGPIPE: 13,
  SIGALRM: 14,
  SIGTERM: 15,
  SIGSTKFLT: 16,
  SIGCHLD: 17,
  SIGCONT: 18,
  SIGSTOP: 19,
  SIGTSTP: 20,
  SIGTTIN: 21,
  SIGTTOU: 22,
  SIGURG: 23,
  SIGXCPU: 24,
  SIGXFSZ: 25,
  SIGVTALRM: 26,
  SIGPROF: 27,
  SIGWINCH: 28,
  SIGIO: 29,
  SIGPOLL: 29,
  SIGPWR: 30,
  SIGSYS: 31,
});

/** The fields of a `CommandResult` (or its `exit` record) that say how a command ended. */
export interface CommandEnding {
  /** The command's own exit code; null after a signal or when it never started. */
  readonly exitCode: number | null;
  /** The signal that ended it, when one did. */
  readonly signal?: string;
  /** The server stopped it at its time limit. */
  readonly timedOut: boolean;
  /** It was cancelled. */
  readonly cancelled: boolean;
  /** Why it could not start, when it could not. */
  readonly error?: string;
}

/** The Linux number of a signal named `SIGTERM`, `TERM` or `15`; undefined when unknown. */
export function signalNumber(name: string | null | undefined): number | undefined {
  const text = (name ?? "").trim().toUpperCase();
  if (text === "") return undefined;
  if (/^[0-9]+$/u.test(text)) return Number(text);
  return LINUX_SIGNALS[text.startsWith("SIG") ? text : `SIG${text}`];
}

/** The shell exit code for how a command ended, by the table above. Always a number. */
export function shellExitCode(result: CommandEnding): number {
  if (result.cancelled) return EXIT_CANCELLED;
  if (result.timedOut) return EXIT_TIMED_OUT;
  if (result.error) return EXIT_FAILED;
  if (result.exitCode !== null && result.exitCode !== undefined) return result.exitCode;
  const number = signalNumber(result.signal);
  return number === undefined ? EXIT_FAILED : EXIT_SIGNAL_BASE + number;
}

/** One line that says how a command ended, when its exit code alone does not; undefined for an ordinary exit. */
export function endingNote(result: CommandEnding, timeoutSeconds?: number): string | undefined {
  if (result.cancelled) return "Command was cancelled";
  if (result.timedOut) return timeoutSeconds !== undefined ? `Command timed out after ${timeoutSeconds} seconds` : "Command timed out";
  if (result.error) return `The command could not start: ${result.error}`;
  if (result.exitCode !== null && result.exitCode !== undefined) return undefined;
  if (signalNumber(result.signal) !== undefined) return `Command was ended by signal ${String(result.signal)}`;
  return result.signal ? `Command ended without an exit code (${result.signal})` : "Command ended without an exit code";
}
