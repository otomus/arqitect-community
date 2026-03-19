/**
 * Browser Click tool -- clicks an element on an open browser page.
 */

import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { chromium, Browser, Page, BrowserContext } from 'playwright';

const CDP_FILE = path.join(process.env.HOME ?? '', '.arqitect_browser_cdp.json');
const PAGES_FILE = path.join(process.env.HOME ?? '', '.arqitect_browser_pages.json');

interface CdpInfo {
  ws_endpoint: string;
}

interface PageMeta {
  url: string;
}

interface PagesInfo {
  [pageId: string]: PageMeta;
}

interface RequestParams {
  page_id?: string;
  selector?: string;
}

interface RpcRequest {
  id?: string | number;
  params?: RequestParams;
}

/**
 * Connect to the shared browser via CDP and retrieve a page by its ID.
 *
 * @param pageId - UUID of the page returned by browser_open
 * @returns Tuple of browser and page
 * @throws Error if no browser is running or the page cannot be found
 */
async function getPage(pageId: string): Promise<{ browser: Browser; page: Page }> {
  if (!fs.existsSync(CDP_FILE)) {
    throw new Error('No browser running. Call browser_open first.');
  }

  const cdpInfo: CdpInfo = JSON.parse(fs.readFileSync(CDP_FILE, 'utf-8'));
  const pagesInfo: PagesInfo = JSON.parse(fs.readFileSync(PAGES_FILE, 'utf-8'));

  if (!(pageId in pagesInfo)) {
    throw new Error(`No page found for page_id '${pageId}'`);
  }

  const pageMeta = pagesInfo[pageId];
  const browser = await chromium.connectOverCDP(cdpInfo.ws_endpoint);

  for (const context of browser.contexts()) {
    for (const page of context.pages()) {
      if (page.url() === pageMeta.url) {
        return { browser, page };
      }
    }
  }

  throw new Error(`Page with URL '${pageMeta.url}' not found in browser`);
}

/**
 * Click the element matching a CSS selector on the given page.
 *
 * @param params - Must contain page_id and selector
 * @returns Object confirming the click action
 * @throws Error if page_id or selector is missing
 */
async function handleRequest(params: RequestParams): Promise<{ clicked: string }> {
  const pageId = params.page_id;
  const selector = params.selector;

  if (!pageId) {
    throw new Error("'page_id' parameter is required");
  }
  if (!selector) {
    throw new Error("'selector' parameter is required");
  }

  const { browser, page } = await getPage(pageId);
  try {
    await page.click(selector);
    return { clicked: selector };
  } finally {
    await browser.close();
  }
}

// -- stdio JSON-RPC loop --
process.stdout.write(JSON.stringify({ ready: true }) + '\n');

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', async (line: string) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  const req: RpcRequest = JSON.parse(trimmed);
  const params = req.params ?? {};
  try {
    const result = await handleRequest(params);
    process.stdout.write(JSON.stringify({ id: req.id, result }) + '\n');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    process.stdout.write(JSON.stringify({ id: req.id, error: msg }) + '\n');
  }
});
