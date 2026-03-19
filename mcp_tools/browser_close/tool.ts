/**
 * Browser Close tool -- closes a browser page and removes it from the registry.
 */

import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { chromium, Browser, Page } from 'playwright';

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
}

interface RpcRequest {
  id?: string | number;
  params?: RequestParams;
}

/**
 * Connect to the shared browser via CDP and retrieve a page by its ID.
 *
 * @param pageId - UUID of the page returned by browser_open
 * @returns Object with browser and page
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
 * Remove a page_id entry from the shared pages JSON file.
 *
 * @param pageId - UUID of the page to remove
 */
function removePageMapping(pageId: string): void {
  if (!fs.existsSync(PAGES_FILE)) {
    return;
  }

  const pagesInfo: PagesInfo = JSON.parse(fs.readFileSync(PAGES_FILE, 'utf-8'));
  delete pagesInfo[pageId];
  fs.writeFileSync(PAGES_FILE, JSON.stringify(pagesInfo));
}

/**
 * Close the page identified by page_id and remove it from the registry.
 *
 * @param params - Must contain page_id
 * @returns Object confirming the page was closed
 * @throws Error if page_id is missing
 */
async function handleRequest(params: RequestParams): Promise<{ closed: string }> {
  const pageId = params.page_id;

  if (!pageId) {
    throw new Error("'page_id' parameter is required");
  }

  const { browser, page } = await getPage(pageId);
  try {
    await page.close();
    removePageMapping(pageId);
    return { closed: pageId };
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
