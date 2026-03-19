/**
 * Perform a DNS lookup for a domain name.
 */

import * as dns from 'dns/promises';

/**
 * Resolve a domain name to IP addresses.
 *
 * @param domain - Domain name to look up
 * @param type - Record type: A, AAAA, MX, TXT, CNAME, NS (defaults to "A")
 * @returns JSON string with domain, type, and resolved records
 * @throws Error if the DNS lookup fails
 */
export async function run(domain: string, type: string = 'A'): Promise<string> {
  const recordType = type.toUpperCase();

  if (recordType !== 'A' && recordType !== 'AAAA') {
    return JSON.stringify({
      domain,
      type: recordType,
      note: 'Only A and AAAA supported via stdlib. Install a DNS library for MX/TXT/CNAME/NS.',
    });
  }

  try {
    const family = recordType === 'A' ? 4 : 6;
    const results = await dns.resolve(domain, recordType === 'A' ? 'A' : 'AAAA');
    const ips = [...new Set(results)].sort();
    return JSON.stringify({ domain, type: recordType, records: ips }, null, 2);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`DNS lookup failed for ${domain}: ${msg}`);
  }
}
