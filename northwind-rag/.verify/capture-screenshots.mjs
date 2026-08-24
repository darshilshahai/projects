import { chromium } from "playwright-core";
import { mkdir } from "node:fs/promises";

const EXECUTABLE =
  "/Users/darshilshah/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
const APP = "http://localhost:3000";
const OUT = "../docs/screenshots";

await mkdir(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: EXECUTABLE });

async function shoot(name, { width = 900, height = 1100, act }) {
  const page = await browser.newPage({
    viewport: { width, height },
    deviceScaleFactor: 2,
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });

  await page.goto(APP, { waitUntil: "networkidle" });
  if (act) await act(page);
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  console.log(
    `${name}: ${errors.length ? "ERRORS -> " + errors.join(" | ") : "clean"}`,
  );
  await page.close();
}

const clickChip = (label) => async (page) => {
  await page.getByRole("button", { name: new RegExp(label, "i") }).click();
  await page.getByRole("heading", { name: /Sources/i }).waitFor({ timeout: 60000 });
  await page.waitForTimeout(500);
};

await shoot("01-home-dark", {});

await shoot("02-grounded-answer", { act: clickChip("sick leave") });

await shoot("03-refused-answer", { act: clickChip("office pets") });

await shoot("04-sources-expanded", {
  act: async (page) => {
    await clickChip("sick leave")(page);
    await page.getByRole("button", { name: "Show full chunk" }).first().click();
    await page.waitForTimeout(200);
  },
});

await shoot("05-light-theme", {
  act: async (page) => {
    await page.getByRole("button", { name: /switch to light/i }).click();
    await page.waitForTimeout(200);
  },
});

await shoot("06-document-upload", {
  act: async (page) => {
    await page.getByRole("button", { name: "PDF", exact: true }).click();
    await page.waitForTimeout(200);
  },
});

await shoot("07-mobile", {
  width: 390,
  height: 844,
  act: clickChip("sick leave"),
});

await browser.close();
