import { expect, test } from "@playwright/test";

for (const scenario of [
  { increment: "5", expected: "allow" },
  { increment: "10", expected: "block" },
] as const) {
  test(`propose, replay, inspect, and record a ${scenario.expected} gate`, async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("status")).toContainText("Ready");
    await expect(page.getByText("100 events · seed 314159")).toBeVisible();

    await page.getByLabel("Candidate increment").selectOption(scenario.increment);
    await page.getByRole("button", { name: "Run comparison" }).click();

    await expect(page.getByText("Policy result")).toBeVisible({ timeout: 30_000 });
    await expect(page.locator(".risk-banner strong")).toHaveText(scenario.expected);
    await expect(page.getByText("maximum delta")).toBeVisible();
    await expect(page.locator(".checksum")).toContainText("sha256:");
    await expect(page.getByText("Simulation ID")).toBeVisible();
    await expect(page.getByText("Baseline rule ID")).toBeVisible();
    await expect(page.getByText("Candidate rule ID")).toBeVisible();
    await expect(page.getByText("Dataset ID")).toBeVisible();
    await expect(page.getByText("Policy ID")).toBeVisible();
    await expect(page.getByText("rounding-engine-v1")).toBeVisible();

    await page.getByRole("button", { name: "Approve evidence" }).click();
    await expect(page.getByText("Release gate")).toBeVisible();
    await expect(page.locator(".gate strong")).toHaveText(scenario.expected);
  });
}
