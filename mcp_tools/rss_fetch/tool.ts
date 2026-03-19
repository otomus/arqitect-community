/**
 * Fetch and parse an RSS or Atom feed using fast-xml-parser.
 */

import { XMLParser } from 'fast-xml-parser';

interface FeedEntry {
  title: string;
  link: string;
  summary: string;
  published: string;
}

interface AtomEntry {
  title?: string;
  link?: { '@_href'?: string } | Array<{ '@_href'?: string }>;
  summary?: string;
  published?: string;
  updated?: string;
}

interface AtomFeed {
  feed?: {
    entry?: AtomEntry | AtomEntry[];
  };
}

interface RssItem {
  title?: string;
  link?: string;
  description?: string;
  pubDate?: string;
}

interface RssFeed {
  rss?: {
    channel?: {
      item?: RssItem | RssItem[];
    };
  };
}

/**
 * Safely extract a string value from an XML-parsed field.
 *
 * @param value - Parsed XML value (may be string, number, or undefined)
 * @returns Trimmed string value or empty string
 */
function safeText(value: unknown): string {
  if (value === undefined || value === null) return '';
  return String(value).trim();
}

/**
 * Extract the href from an Atom link element (may be object or array).
 *
 * @param link - Parsed link element
 * @returns The href string or empty string
 */
function extractAtomLink(link: unknown): string {
  if (!link) return '';
  if (Array.isArray(link)) {
    return (link[0] as Record<string, string>)?.['@_href'] ?? '';
  }
  if (typeof link === 'object') {
    return (link as Record<string, string>)['@_href'] ?? '';
  }
  return String(link);
}

/**
 * Fetch an RSS/Atom feed and return entries as JSON.
 *
 * @param url - URL of the RSS/Atom feed
 * @returns JSON string of feed entries
 * @throws Error if the fetch or parse fails
 */
export async function run(url: string): Promise<string> {
  const response = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
    signal: AbortSignal.timeout(15000),
  });
  const raw = await response.text();

  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
  });
  const parsed = parser.parse(raw) as AtomFeed & RssFeed;

  const entries: FeedEntry[] = [];

  // Handle Atom feeds
  const atomFeed = parsed.feed;
  if (atomFeed?.entry) {
    const atomEntries = Array.isArray(atomFeed.entry) ? atomFeed.entry : [atomFeed.entry];
    for (const entry of atomEntries) {
      entries.push({
        title: safeText(entry.title),
        link: extractAtomLink(entry.link),
        summary: safeText(entry.summary),
        published: safeText(entry.published) || safeText(entry.updated),
      });
    }
    return JSON.stringify(entries, null, 2);
  }

  // Handle RSS 2.0 feeds
  const channel = parsed.rss?.channel;
  if (channel?.item) {
    const items = Array.isArray(channel.item) ? channel.item : [channel.item];
    for (const item of items) {
      entries.push({
        title: safeText(item.title),
        link: safeText(item.link),
        summary: safeText(item.description),
        published: safeText(item.pubDate),
      });
    }
  }

  return JSON.stringify(entries, null, 2);
}
