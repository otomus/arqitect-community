/**
 * Browser Open tool -- launches a headless browser and navigates to a URL.
 */

import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { chromium, Browser } from 'playwright';

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
  url?: string;
  wait?: string;
}

interface RpcRequest {
  id?: string | number;
  params?: RequestParams;
}

// Global state: single browser instance shared across calls within this long-lived process.
let activeBrowser: Browser | null = null;

/**
 * Lazily start Playwright and launch a headless Chromium browser.
 * If a CDP endpoint file already exists and the browser is still reachable,
 * reconnect to it. Otherwise launch a fresh browser and persist its CDP
 * websocket endpoint.
 *
 * @returns A connected Browser instance
 */
async function ensureBrowser(): Promise<Browser> {
  if (activeBrowser !== null) {
    return activeBrowser;
  }

  // Try to reconnect to an existing browser first
  if (fs.existsSync(CDP_FILE)) {
    try {
      const cdpInfo: CdpInfo = JSON.parse(fs.readFileSync(CDP_FILE, 'utf-8'));
      activeBrowser = await chromium.connectOverCDP(cdpInfo.ws_endpoint);
      return activeBrowser;
    } catch {
      // Browser is gone -- launch a new one
    }
  }

  activeBrowser = await chromium.launch({ headless: true });

  // Persist the CDP websocket endpoint so other tools can connect
  const wsEndpoint = activeBrowser.contexts()[0]?.pages()[0]?.url()
    ? (activeBrowser as Record<string, unknown>)['_wsEndpoint'] as string
    : '';

  // Access internal ws endpoint via Playwright internals
  const browserServer = (activeBrowser as Record<string, unknown>)['_connection'] as Record<string, unknown> | undefined;
  let endpoint = '';
  if (browserServer && typeof browserServer === 'object') {
    endpoint = (browserServer as Record<string, unknown>)['_wsEndpoint'] as string ?? '';
  }

  // For launched browsers, we need to get the WS endpoint from the browser process
  const wsUrl = (activeBrowser as unknown as { wsEndpoint?: () => string }).wsEndpoint?.() ?? endpoint;

  fs.writeFileSync(CDP_FILE, JSON.stringify({ ws_endpoint: wsUrl }));

  return activeBrowser;
}

/**
 * Persist page_id to URL mapping to the shared pages JSON file.
 *
 * @param pageId - UUID for the new page
 * @param url - URL that the page navigated to
 */
function savePageMapping(pageId: string, url: string): void {
  let pagesInfo: PagesInfo = {};
  if (fs.existsSync(PAGES_FILE)) {
    pagesInfo = JSON.parse(fs.readFileSync(PAGES_FILE, 'utf-8'));
  }

  pagesInfo[pageId] = { url };
  fs.writeFileSync(PAGES_FILE, JSON.stringify(pagesInfo));
}

/**
 * Open a new page, navigate to the URL, optionally wait for a CSS selector.
 *
 * @param params - Must contain url. May contain wait (CSS selector).
 * @returns Object with page_id -- a UUID identifying the opened page
 * @throws Error if url is missing
 */
async function handleRequest(params: RequestParams): Promise<{ page_id: string }> {
  const url = params.url;
  if (!url) {
    throw new Error("'url' parameter is required");
  }

  const waitSelector = params.wait;
  const browser = await ensureBrowser();
  const page = await browser.newPage();
  await page.goto(url);

  if (waitSelector) {
    await page.waitForSelector(waitSelector);
  }

  const pageId = crypto.randomUUID();

  // Persist the mapping so other subprocess tools can find this page
  savePageMapping(pageId, page.url());

  return { page_id: pageId };
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
