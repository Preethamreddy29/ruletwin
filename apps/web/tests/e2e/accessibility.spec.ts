import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function expectNoSeriousAccessibilityViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical",
  );
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
}

test("pilot workflow has no serious or critical accessibility violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Ready");
  await expectNoSeriousAccessibilityViolations(page);

  await page.getByLabel("Candidate increment").selectOption("5");
  await page.getByRole("button", { name: "Run comparison" }).click();
  await expect(page.getByText("Policy result")).toBeVisible({ timeout: 30_000 });
  await expectNoSeriousAccessibilityViolations(page);
});

test("pilot identity and primary action remain keyboard reachable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Ready");
  await expect(page.getByLabel("Active synthetic persona")).toBeVisible();

  await page.getByLabel("Active synthetic persona").focus();
  await expect(page.getByLabel("Active synthetic persona")).toBeFocused();
  await page.getByLabel("Candidate increment").focus();
  await expect(page.getByLabel("Candidate increment")).toBeFocused();
  await page.getByRole("button", { name: "Run comparison" }).focus();
  await expect(page.getByRole("button", { name: "Run comparison" })).toBeFocused();
  await expectNoSeriousAccessibilityViolations(page);
});
