// Turn assets/linkedin/banner.svg into the PNG LinkedIn accepts, frozen at the
// moment named by the SVG's data-still attribute (seconds into the map loop).
//
//   python3 tools/build_worldmap.py && node tools/render_banner.js
//
// Needs Playwright with Chromium (npm i playwright && npx playwright install chromium).

const path = require("path");
const { chromium } = require("playwright");

const svgPath = path.join(__dirname, "..", "assets", "linkedin", "banner.svg");
const pngPath = svgPath.replace(/\.svg$/, ".png");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1584, height: 396 } });
  await page.goto("file://" + svgPath);
  await page.evaluate(() => {
    const svg = document.documentElement;
    svg.pauseAnimations();
    svg.setCurrentTime(Number(svg.dataset.still));
  });
  await page.screenshot({ path: pngPath });
  await browser.close();
  console.log(path.relative(process.cwd(), pngPath));
})();
