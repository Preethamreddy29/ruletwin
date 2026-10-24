import { expect, test } from "@playwright/test";

for (const scenario of [
  { increment: "5", expected: "allow" },
  { increment: "10", expected: "block" },
] as const) {
  test(`tenant-scoped personas record a ${scenario.expected} gate`, async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("status")).toContainText("Ready");
    await expect(page.getByText("100 events · seed 314159")).toBeVisible();

    await page.getByLabel("Candidate increment").selectOption(scenario.increment);
    await page.getByRole("button", { name: "Run comparison" }).click();
    await expect(page.getByText("Policy result")).toBeVisible({ timeout: 30_000 });
    await expect(page.locator(".risk-banner strong")).toHaveText(scenario.expected);
    await expect(page.locator(".checksum")).toContainText("sha256:");

    await page.getByLabel("Active synthetic persona").selectOption("brightline-reviewer");
    await expect(page.getByText("Evidence is hidden after the tenant switch")).toBeVisible();
    await page.getByRole("button", { name: "Attempt cross-tenant access" }).click();
    await expect(page.getByText(/indistinguishable from an absent object/)).toBeVisible();

    await page.getByLabel("Active synthetic persona").selectOption("novabill-reviewer");
    await page.getByRole("button", { name: "Approve evidence as QA" }).click();
    await expect(page.getByRole("button", { name: "Evidence reviewed" })).toBeDisabled();

    await page.getByLabel("Active synthetic persona").selectOption("novabill-approver");
    await page.getByRole("button", { name: "Evaluate release gate" }).click();
    await expect(page.getByText("Release gate")).toBeVisible();
    await expect(page.locator(".gate strong")).toHaveText(scenario.expected);

    await page.getByLabel("Active synthetic persona").selectOption("novabill-auditor");
    await page.getByRole("button", { name: "Inspect tenant audit trail" }).click();
    await expect(page.getByText(/Authorized audit events:/)).toBeVisible();
  });
}
