/**
 * Send an HTTP PUT request to a URL and return the response body.
 */

/**
 * Send a PUT request and return the response body.
 *
 * @param url - URL to send the request to
 * @param body - Request body (JSON string)
 * @param headers - JSON string of headers to include (defaults to "{}")
 * @returns Response body as a string
 * @throws Error if the request fails
 */
export async function run(url: string, body: string, headers: string = '{}'): Promise<string> {
  const hdrs: Record<string, string> = JSON.parse(headers);
  if (!('Content-Type' in hdrs)) {
    hdrs['Content-Type'] = 'application/json';
  }
  const response = await fetch(url, {
    method: 'PUT',
    headers: hdrs,
    body,
    signal: AbortSignal.timeout(30000),
  });
  return await response.text();
}
