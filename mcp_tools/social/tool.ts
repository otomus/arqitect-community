/**
 * Unified social media management: post, read, search, reply, like, followers, and trending.
 *
 * Supports Twitter and Mastodon platforms via their respective APIs.
 * Requires platform-specific API keys set as env vars:
 *   ARQITECT_TWITTER_API_KEY, ARQITECT_MASTODON_API_KEY, ARQITECT_MASTODON_INSTANCE
 */

import * as readline from 'readline';

const VALID_OPERATIONS = new Set([
  'post', 'read', 'search', 'reply', 'like', 'followers', 'trending',
]);

const TWITTER_API_KEY = process.env.ARQITECT_TWITTER_API_KEY ?? '';
const MASTODON_API_KEY = process.env.ARQITECT_MASTODON_API_KEY ?? '';
const MASTODON_INSTANCE = process.env.ARQITECT_MASTODON_INSTANCE ?? 'https://mastodon.social';

const REQUEST_TIMEOUT_MS = 10000;

interface RequestParams {
  operation?: string;
  platform?: string;
  post_id?: string;
  content?: string;
  query?: string;
  user?: string;
  media?: string;
  reaction?: string;
  region?: string;
}

interface RpcRequest {
  id?: string | number;
  params?: RequestParams;
}

interface SocialResult {
  [key: string]: unknown;
}

/**
 * Resolve the API key for a given platform.
 *
 * @param platform - Platform name (lowercase)
 * @returns API key string
 * @throws Error if no API key is configured
 */
function getApiKey(platform: string): string {
  if (platform === 'twitter') {
    if (!TWITTER_API_KEY) {
      throw new Error('Set ARQITECT_TWITTER_API_KEY environment variable for Twitter access');
    }
    return TWITTER_API_KEY;
  }
  if (platform === 'mastodon') {
    if (!MASTODON_API_KEY) {
      throw new Error('Set ARQITECT_MASTODON_API_KEY environment variable for Mastodon access');
    }
    return MASTODON_API_KEY;
  }
  throw new Error(`Unsupported platform: ${platform}. Supported: twitter, mastodon`);
}

/**
 * Get the instance URL for federated platforms.
 *
 * @param platform - Platform name (lowercase)
 * @returns Instance URL string
 */
function getInstance(platform: string): string {
  if (platform === 'mastodon') return MASTODON_INSTANCE;
  return '';
}

/**
 * Map common region codes to Twitter WOEIDs.
 *
 * @param region - Two-letter country code
 * @returns WOEID integer
 */
function regionToWoeid(region: string): number {
  const regionMap: Record<string, number> = {
    US: 23424977,
    UK: 23424975,
    JP: 23424856,
    DE: 23424829,
    FR: 23424819,
    BR: 23424768,
  };
  return regionMap[region.toUpperCase()] ?? 1;
}

/**
 * Create a new social media post.
 *
 * @param params - Must contain 'platform' and 'content'
 * @returns Object with status and post details
 */
async function handlePost(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const content = params.content;
  if (!content) throw new Error('content is required for post operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const response = await fetch('https://api.twitter.com/2/tweets', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: content }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const data = await response.json() as Record<string, Record<string, string>>;
    return { status: 'posted', platform, post_id: data.data?.id ?? '' };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const response = await fetch(`${instance}/api/v1/statuses`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: content }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Record<string, string>;
    return { status: 'posted', platform, post_id: data.id ?? '' };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Read a specific post by ID.
 *
 * @param params - Must contain 'platform' and 'post_id'
 * @returns Object with post content and metadata
 */
async function handleRead(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const postId = params.post_id;
  if (!postId) throw new Error('post_id is required for read operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const url = `https://api.twitter.com/2/tweets/${postId}?tweet.fields=created_at,author_id,text`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const json = await response.json() as Record<string, unknown>;
    return { status: 'ok', platform, post: json.data ?? {} };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const response = await fetch(`${instance}/api/v1/statuses/${postId}`, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Record<string, unknown>;
    const account = (data.account as Record<string, string>) ?? {};
    return {
      status: 'ok',
      platform,
      post: {
        id: data.id,
        content: data.content,
        created_at: data.created_at,
        account: account.acct ?? '',
      },
    };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Search for posts matching a query.
 *
 * @param params - Must contain 'platform' and 'query'
 * @returns Object with matching posts
 */
async function handleSearch(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const query = params.query;
  if (!query) throw new Error('query is required for search operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const url = `https://api.twitter.com/2/tweets/search/recent?query=${encodeURIComponent(query)}&max_results=10`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const data = await response.json() as Record<string, unknown[]>;
    const posts = data.data ?? [];
    return { status: 'ok', platform, query, count: posts.length, posts };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const url = `${instance}/api/v2/search?q=${encodeURIComponent(query)}&type=statuses&limit=10`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Record<string, Array<Record<string, unknown>>>;
    const statuses = data.statuses ?? [];
    const posts = statuses.map((s) => ({
      id: s.id,
      content: s.content,
      account: ((s.account as Record<string, string>) ?? {}).acct ?? '',
    }));
    return { status: 'ok', platform, query, count: posts.length, posts };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Reply to a specific post.
 *
 * @param params - Must contain 'platform', 'post_id', and 'content'
 * @returns Object with status and reply details
 */
async function handleReply(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const postId = params.post_id;
  const content = params.content;
  if (!postId) throw new Error('post_id is required for reply operation');
  if (!content) throw new Error('content is required for reply operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const response = await fetch('https://api.twitter.com/2/tweets', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: content, reply: { in_reply_to_tweet_id: postId } }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const data = await response.json() as Record<string, Record<string, string>>;
    return { status: 'replied', platform, reply_id: data.data?.id ?? '' };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const response = await fetch(`${instance}/api/v1/statuses`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: content, in_reply_to_id: postId }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Record<string, string>;
    return { status: 'replied', platform, reply_id: data.id ?? '' };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Like/favourite a post.
 *
 * @param params - Must contain 'platform' and 'post_id'
 * @returns Object confirming the like
 */
async function handleLike(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const postId = params.post_id;
  if (!postId) throw new Error('post_id is required for like operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const response = await fetch('https://api.twitter.com/2/users/me/likes', {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ tweet_id: postId }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
  } else if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const response = await fetch(`${instance}/api/v1/statuses/${postId}/favourite`, {
      method: 'POST',
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
  } else {
    throw new Error(`Unsupported platform: ${platform}`);
  }

  return { status: 'liked', platform, post_id: postId };
}

/**
 * Get follower count and info for a user.
 *
 * @param params - Must contain 'platform' and 'user'
 * @returns Object with follower count and user metadata
 */
async function handleFollowers(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const username = params.user;
  if (!username) throw new Error('user is required for followers operation');

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const url = `https://api.twitter.com/2/users/by/username/${username}?user.fields=public_metrics`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const json = await response.json() as Record<string, Record<string, Record<string, number>>>;
    const data = json.data ?? {};
    const metrics = (data as Record<string, unknown>).public_metrics as Record<string, number> ?? {};
    return {
      platform,
      username,
      followers: metrics.followers_count ?? 0,
      following: metrics.following_count ?? 0,
    };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const url = `${instance}/api/v1/accounts/lookup?acct=${encodeURIComponent(username)}`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Record<string, unknown>;
    return {
      platform,
      username,
      followers: (data.followers_count as number) ?? 0,
      following: (data.following_count as number) ?? 0,
      display_name: (data.display_name as string) ?? '',
    };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

/**
 * Get trending topics on a platform.
 *
 * @param params - Must contain 'platform'. Optionally 'region'.
 * @returns Object with list of trending topics
 */
async function handleTrending(params: RequestParams): Promise<SocialResult> {
  const platform = params.platform!.toLowerCase();
  const apiKey = getApiKey(platform);
  const region = params.region ?? '';

  const headers: Record<string, string> = { Authorization: `Bearer ${apiKey}` };

  if (platform === 'twitter') {
    const woeid = region ? regionToWoeid(region) : 1;
    const url = `https://api.twitter.com/1.1/trends/place.json?id=${woeid}`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Twitter API error: ${response.status}`);
    const data = await response.json() as Array<Record<string, Array<Record<string, unknown>>>>;
    const trends = (data[0].trends ?? []).map((t) => ({
      name: t.name as string,
      tweet_volume: t.tweet_volume as number | null,
    }));
    return { platform, region: region || 'worldwide', trends };
  }

  if (platform === 'mastodon') {
    const instance = getInstance(platform);
    const url = `${instance}/api/v1/trends/tags`;
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`Mastodon API error: ${response.status}`);
    const data = await response.json() as Array<Record<string, unknown>>;
    const trends = data.map((t) => {
      const history = (t.history as Array<Record<string, unknown>>) ?? [{}];
      return {
        name: `#${t.name as string}`,
        uses: (history[0]?.uses as number) ?? 0,
      };
    });
    return { platform, region: region || 'global', trends };
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

const HANDLERS: Record<string, (params: RequestParams) => Promise<SocialResult>> = {
  post: handlePost,
  read: handleRead,
  search: handleSearch,
  reply: handleReply,
  like: handleLike,
  followers: handleFollowers,
  trending: handleTrending,
};

// -- stdio JSON-RPC loop --
process.stdout.write(JSON.stringify({ ready: true }) + '\n');

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', async (line: string) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  const req: RpcRequest = JSON.parse(trimmed);
  const params = req.params ?? {};
  try {
    const operation = params.operation ?? '';
    if (!VALID_OPERATIONS.has(operation)) {
      throw new Error(
        `Invalid operation: '${operation}'. Must be one of: ${[...VALID_OPERATIONS].sort().join(', ')}`
      );
    }
    const platform = params.platform ?? '';
    if (!platform) {
      throw new Error('platform is required');
    }
    const handler = HANDLERS[operation];
    const result = await handler(params);
    process.stdout.write(JSON.stringify({ id: req.id, result: JSON.stringify(result, null, 2) }) + '\n');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    process.stdout.write(JSON.stringify({ id: req.id, error: msg }) + '\n');
  }
});
