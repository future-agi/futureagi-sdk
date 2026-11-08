// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
/**
 * BoundedExecutor behaves as a ThreadPoolExecutor which will block on
 * calls to submit() once the limit given as "bound" work items are queued for
 * execution.
 * @param bound - Integer - the maximum number of items in the work queue
 * @param maxWorkers - Integer - the size of the thread pool
 */
export declare class BoundedExecutor {
    constructor(bound: number, maxWorkers: number);
    /**
     * Submit a function for execution
     */
    submit<T>(fn: (...args: any[]) => T | Promise<T>, ...args: any[]): Promise<T>;
    /**
     * Shutdown the executor
     */
    shutdown(wait?: boolean): Promise<void>;
}
