/**
 * Search the web using DuckDuckGo HTML search.
 */

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

/**
 * Search DuckDuckGo and return top 10 results as JSON.
 *
 * @param query - Search query string
 * @param engine - Search engine to use (defaults to "duckduckgo")
 * @returns JSON string of search results
 * @throws Error if the search request fails
 */
export async function run(query: string, engine: string = 'duckduckgo'): Promise<string> {
  const encodedQuery = encodeURIComponent(query);
  const url = `https://html.duckduckgo.com/html/?q=${encodedQuery}`;
  const response = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
    signal: AbortSignal.timeout(15000),
  });
  const html = await response.text();

  const results: SearchResult[] = [];

  // DuckDuckGo HTML results are in <a class="result__a"> tags
  const blockPattern = /<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>.*?<a[^>]+class="result__snippet"[^>]*>(.*?)<\/a>/gs;

  let match: RegExpExecArray | null;
  while ((match = blockPattern.exec(html)) !== null && results.length < 10) {
    const href = match[1];
    const titleHtml = match[2];
    const snippetHtml = match[3];

    const title = titleHtml.replace(/<[^>]+>/g, '').trim();
    const snippet = snippetHtml.replace(/<[^>]+>/g, '').trim();

    // DuckDuckGo wraps URLs in a redirect; extract the actual URL
    const urlMatch = /uddg=([^&]+)/.exec(href);
    const actualUrl = urlMatch ? decodeURIComponent(urlMatch[1]) : href;

    results.push({ title, url: actualUrl, snippet });
  }

  return JSON.stringify(results, null, 2);
}
