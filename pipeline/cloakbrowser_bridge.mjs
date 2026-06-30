#!/usr/bin/env node
/**
 * CloakBrowser bridge — resolves a URL through redirects and extracts visible text.
 *
 * Usage: node cloakbrowser_bridge.mjs <url>
 * Output: JSON { url, title, text, content_length } or { error }
 *
 * ponytail: single URL, single page, no concurrency.
 */
import { launch } from "/usr/local/lib/node_modules/cloakbrowser/dist/index.js";

const url = process.argv[2];
if (!url) {
  console.log(JSON.stringify({ error: "No URL provided" }));
  process.exit(1);
}

let browser;
try {
  browser = await launch({ headless: true });
  const page = await browser.newPage();

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
  await page.waitForTimeout(3000);

  const finalUrl = page.url();
  const title = await page.title();

  const text = await page.evaluate(() => {
    const article = document.querySelector("article, main, [role='main']");
    if (article) {
      const ps = article.querySelectorAll("p");
      if (ps.length > 0) {
        const body = Array.from(ps).map((e) => e.innerText || "").join("\n\n");
        if (body.length > 100) return body;
      }
      const inner = article.innerText || "";
      if (inner.length > 100) return inner;
    }
    return document.body ? document.body.innerText : "";
  });

  console.log(JSON.stringify({
    url: finalUrl,
    title: title || "",
    text: text.substring(0, 100_000),
    content_length: text.length,
  }));
} catch (err) {
  console.log(JSON.stringify({ error: err.message || String(err) }));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
}
