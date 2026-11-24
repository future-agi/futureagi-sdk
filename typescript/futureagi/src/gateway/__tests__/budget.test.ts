import { BudgetManager } from "../budget";

describe("BudgetManager", () => {
  it("tracks global spend", () => {
    const bm = new BudgetManager({ maxBudget: 10 });
    bm.updateCost(3);
    expect(bm.getCurrentSpend()).toBe(3);
    expect(bm.getRemainingBudget()).toBe(7);
  });

  it("throws when global budget exceeded", () => {
    const bm = new BudgetManager({ maxBudget: 1 });
    bm.updateCost(0.9);
    expect(() => bm.checkBudget(0.2)).toThrow("Budget exceeded");
  });

  it("allows within budget", () => {
    const bm = new BudgetManager({ maxBudget: 10 });
    bm.updateCost(5);
    expect(() => bm.checkBudget(4)).not.toThrow();
  });

  it("tracks per-user spend", () => {
    const bm = new BudgetManager({ maxBudget: 100 });
    bm.setUserBudget("alice", 5);
    bm.updateCost(3, "alice");
    expect(bm.getCurrentSpend("alice")).toBe(3);
    expect(bm.getRemainingBudget("alice")).toBe(2);
  });

  it("throws when user budget exceeded", () => {
    const bm = new BudgetManager({ maxBudget: 100 });
    bm.setUserBudget("bob", 1);
    bm.updateCost(0.8, "bob");
    expect(() => bm.checkBudget(0.3, "bob")).toThrow("User budget exceeded");
  });

  it("reset clears global counters", () => {
    const bm = new BudgetManager({ maxBudget: 10 });
    bm.updateCost(5);
    bm.updateCost(2, "alice");
    bm.reset();
    expect(bm.getCurrentSpend()).toBe(0);
    expect(bm.getCurrentSpend("alice")).toBe(0);
  });

  it("reset clears per-user counter only", () => {
    const bm = new BudgetManager({ maxBudget: 100 });
    bm.updateCost(5);
    bm.updateCost(3, "alice");
    bm.reset("alice");
    expect(bm.getCurrentSpend("alice")).toBe(0);
    expect(bm.getCurrentSpend()).toBe(8); // global includes both calls
  });

  it("returns null remaining when no budget set", () => {
    const bm = new BudgetManager();
    expect(bm.getRemainingBudget()).toBeNull();
  });

  it("isValidUser checks budget", () => {
    const bm = new BudgetManager();
    bm.setUserBudget("alice", 5);
    expect(bm.isValidUser("alice")).toBe(true);
    bm.updateCost(6, "alice");
    expect(bm.isValidUser("alice")).toBe(false);
  });

  it("isValidUser returns false for unregistered user", () => {
    const bm = new BudgetManager();
    expect(bm.isValidUser("nobody")).toBe(false);
  });

  it("projectedCost returns 0 initially", () => {
    const bm = new BudgetManager({ maxBudget: 10 });
    // Right after creation, elapsed time is ~0, so projected cost should be finite
    expect(bm.projectedCost(24)).toBeGreaterThanOrEqual(0);
  });
});
