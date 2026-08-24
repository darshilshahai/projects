import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "../screenshots");
const baseUrl = "http://localhost:3000";

async function capture(page, name, options = {}) {
  const filePath = path.join(outDir, `${name}.png`);
  await page.screenshot({ path: filePath, fullPage: false, ...options });
  console.log(`Saved ${filePath}`);
}

async function main() {
  await mkdir(outDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await capture(page, "01-landing-hero");

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.55));
  await page.waitForTimeout(500);
  await capture(page, "02-landing-product-preview");

  await page.goto(`${baseUrl}/workspace`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await capture(page, "03-workspace");

  const datasetItem = page.locator('[class*="border-accent"]').first();
  if (await datasetItem.count()) {
    await datasetItem.click().catch(() => {});
    await page.waitForTimeout(500);
  }

  const exampleButton = page.getByRole("button", { name: /revenue/i }).first();
  if (await exampleButton.count()) {
    await exampleButton.click().catch(() => {});
    await page.waitForTimeout(500);
  }

  const runButton = page.getByRole("button", { name: /RUN ANALYSIS/i });
  if (await runButton.count()) {
    await runButton.click().catch(() => {});
    await page.waitForTimeout(12000);
    await capture(page, "04-workspace-analysis");
  }

  await page.goto(`${baseUrl}/evaluation`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await capture(page, "05-evaluation-dashboard");

  await page.evaluate(() => window.scrollBy(0, 900));
  await page.waitForTimeout(400);
  await capture(page, "06-evaluation-benchmark-table");

  const failFilter = page.getByRole("button", { name: /^Failed$/i });
  if (await failFilter.count()) {
    await failFilter.click();
    await page.waitForTimeout(300);
  }

  const firstRow = page.locator("tbody tr").first();
  if (await firstRow.count()) {
    await firstRow.click();
    await page.waitForTimeout(400);
    await capture(page, "07-evaluation-case-inspector");
  }

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
