import { chromium } from "playwright-core";

const EXECUTABLE =
  "/Users/darshilshah/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing";
const APP = "http://localhost:3000";

const browser = await chromium.launch({ executablePath: EXECUTABLE });

async function shoot(name, { width = 900, height = 900, act }) {
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
  await page.screenshot({ path: `shots/${name}.png`, fullPage: true });
  console.log(
    `${name}: ${errors.length ? "ERRORS -> " + errors.join(" | ") : "clean"}`,
  );
  await page.close();
}

const clickChip = (label) => async (page) => {
  await page.getByRole("button", { name: new RegExp(label, "i") }).click();
  await page.getByText(/ms$/).first().waitFor({ timeout: 15000 });
  await page.waitForTimeout(300);
};

await shoot("01-idle", {});

await shoot("02-grounded", { act: clickChip("sick leave") });

await shoot("03-refused", { act: clickChip("office pets") });

await shoot("04-expanded", {
  act: async (page) => {
    await clickChip("sick leave")(page);
    await page.getByRole("button", { name: "Show full chunk" }).first().click();
    await page.waitForTimeout(200);
  },
});

await shoot("05-empty-input", {
  act: async (page) => {
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.waitForTimeout(200);
  },
});

await shoot("06-mobile", {
  width: 390,
  height: 844,
  act: clickChip("sick leave"),
});

await browser.close();
