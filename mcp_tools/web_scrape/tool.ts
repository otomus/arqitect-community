/**
 * Fetch a web page and extract text content using cheerio for HTML parsing.
 */

import * as cheerio from 'cheerio';

/**
 * Extract text from elements matching a basic CSS selector.
 *
 * @param html - Raw HTML string
 * @param selector - CSS selector (tag, .class, #id)
 * @returns Extracted text joined by newlines
 */
function extractBySelector(html: string, selector: string): string {
  const $ = cheerio.load(html);
  const parts: string[] = [];
  $(selector).each((_index, element) => {
    const text = $(element).text().trim();
    if (text) {
      parts.push(text);
    }
  });
  return parts.join('\n');
}

/**
 * Extract all visible text from an HTML page, excluding script/style content.
 *
 * @param html - Raw HTML string
 * @returns Extracted visible text
 */
function extractAllText(html: string): string {
  const $ = cheerio.load(html);
  $('script, style, noscript').remove();
  const text = $('body').text();
  const lines = text.split('\n');
  const parts: string[] = [];
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped) {
      parts.push(stripped);
    }
  }
  return parts.join('\n');
}

/**
 * Fetch a web page and return extracted text.
 *
 * @param url - URL of the page to scrape
 * @param selector - Optional CSS selector to filter elements (supports tag, .class, #id)
 * @returns Extracted text content
 * @throws Error if the fetch fails
 */
export async function run(url: string, selector: string = ''): Promise<string> {
  const response = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
    signal: AbortSignal.timeout(20000),
  });
  const html = await response.text();

  if (selector) {
    return extractBySelector(html, selector);
  }

  return extractAllText(html);
}
