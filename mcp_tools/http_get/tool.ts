/**
 * Send an HTTP GET request to a URL and return the response body.
 */

/**
 * Send a GET request and return the response body.
 *
 * @param url - URL to send the GET request to
 * @param headers - JSON string of headers to include (defaults to "{}")
 * @returns Response body as a string
 * @throws Error if the request fails
 */
export async function run(url: string, headers: string = '{}'): Promise<string> {
  const hdrs: Record<string, string> = JSON.parse(headers);
  const response = await fetch(url, {
    method: 'GET',
    headers: hdrs,
    signal: AbortSignal.timeout(30000),
  });
  return await response.text();
}
