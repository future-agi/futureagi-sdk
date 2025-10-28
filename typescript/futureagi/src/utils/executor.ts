import { setTimeout } from "timers/promises";


/**
 * BoundedExecutor behaves as a ThreadPoolExecutor which will block on
 * calls to submit() once the limit given as "bound" work items are queued for
 * execution.
 * @param bound - Integer - the maximum number of items in the work queue
 * @param maxWorkers - Integer - the size of the thread pool
 */
export class BoundedExecutor {
    private workers: Set<Promise<void>> = new Set();
    private queue: Array<() => Promise<void>> = [];
    private semaphore: number;
    private maxWorkers: number;
    private isShutdown: boolean = false;

    constructor(bound: number, maxWorkers: number) {
        this.semaphore = bound + maxWorkers;
        this.maxWorkers = maxWorkers;
    }

    /**
     * Submit a function for execution
     */
    async submit<T>(fn: (...args: any[]) => T | Promise<T>, ...args: any[]): Promise<T> {
        if (this.isShutdown) {
            throw new Error('Executor has been shutdown');
        }

        // Acquire semaphore
        await this.acquireSemaphore();

        return new Promise<T>((resolve, reject) => {
            const task = async () => {
                try {
                    const result = await fn(...args);
                    resolve(result);
                } catch (error) {
                    reject(error);
                } finally {
                    this.releaseSemaphore();
                }
            };

            if (this.workers.size < this.maxWorkers) {
                // Start worker immediately
                this.startWorker(task);
            } else {
                // Queue the task
                this.queue.push(task);
            }
        });
    }

    /**
     * Shutdown the executor
     */
    async shutdown(wait: boolean = true): Promise<void> {
        this.isShutdown = true;
        
        if (wait) {
            // Wait for all workers to complete
            await Promise.all(Array.from(this.workers));
        }
    }

    private async acquireSemaphore(): Promise<void> {
        while (this.semaphore <= 0) {
            await setTimeout(1);
        }
        this.semaphore--;
    }

    private releaseSemaphore(): void {
        this.semaphore++;
    }

    private startWorker(task: () => Promise<void>): void {
        const workerPromise = this.runWorker(task);
        this.workers.add(workerPromise);
        
        workerPromise.finally(() => {
            this.workers.delete(workerPromise);
        });
    }

    private async runWorker(initialTask: () => Promise<void>): Promise<void> {
        let currentTask: (() => Promise<void>) | undefined = initialTask;

        while (currentTask && !this.isShutdown) {
            await currentTask();
            currentTask = this.queue.shift();
        }
    }
}
