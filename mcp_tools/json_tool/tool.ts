/**
 * Parse, format, or query JSON data.
 */

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

/**
 * Parse a JSON string and return a pretty-printed representation.
 *
 * @param text - JSON string to parse
 * @returns Pretty-printed JSON string
 */
function parseJson(text: string): string {
  const parsed: JsonValue = JSON.parse(text);
  return JSON.stringify(parsed, null, 2);
}

/**
 * Format a JSON string with sorted keys and indentation.
 *
 * @param text - JSON string to format
 * @param indent - Number of spaces for indentation (defaults to 2)
 * @returns Formatted JSON string with sorted keys
 */
function formatJson(text: string, indent: string): string {
  const indentValue = indent ? parseInt(indent, 10) : 2;
  const parsed: JsonValue = JSON.parse(text);
  return JSON.stringify(parsed, Object.keys(parsed as object).sort(), indentValue);
}

/**
 * Sort all keys in a JSON value recursively, for use with JSON.stringify replacer.
 *
 * @param value - Parsed JSON value
 * @returns Value with all object keys sorted
 */
function sortKeysDeep(value: JsonValue): JsonValue {
  if (value === null || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map(sortKeysDeep);
  const sorted: { [key: string]: JsonValue } = {};
  for (const key of Object.keys(value).sort()) {
    sorted[key] = sortKeysDeep((value as { [key: string]: JsonValue })[key]);
  }
  return sorted;
}

/**
 * Format JSON with deep-sorted keys.
 *
 * @param text - JSON string to format
 * @param indent - Number of spaces for indentation
 * @returns Formatted JSON with all keys sorted at all levels
 */
function formatJsonSorted(text: string, indent: string): string {
  const indentValue = indent ? parseInt(indent, 10) : 2;
  const parsed: JsonValue = JSON.parse(text);
  const sorted = sortKeysDeep(parsed);
  return JSON.stringify(sorted, null, indentValue);
}

/**
 * Extract a value from JSON using a dot-notation path.
 *
 * @param text - JSON string to query
 * @param query - Dot-notation path (e.g. "foo.bar.0.baz")
 * @returns Extracted value as a string
 * @throws Error if a key cannot be traversed
 */
function queryJson(text: string, query: string): string {
  const data: JsonValue = JSON.parse(text);
  const parts = query.split('.');
  let current: JsonValue = data;

  for (const part of parts) {
    if (Array.isArray(current)) {
      current = current[parseInt(part, 10)];
    } else if (current !== null && typeof current === 'object') {
      current = (current as { [key: string]: JsonValue })[part];
    } else {
      throw new Error(`Cannot traverse into ${typeof current} with key '${part}'`);
    }
  }

  if (current !== null && typeof current === 'object') {
    return JSON.stringify(current, null, 2);
  }
  return String(current);
}

/**
 * Parse, pretty-print, or query a JSON string.
 *
 * @param input - JSON string to process
 * @param operation - Operation to perform: 'parse', 'format', or 'query'
 * @param query - Dot-notation path for the query operation
 * @param indent - Number of spaces for indentation (format only, defaults to "2")
 * @returns Processed JSON string or extracted value
 * @throws Error if the operation is invalid
 */
export function run(input: string, operation: string, query: string = '', indent: string = ''): string {
  if (operation === 'parse') {
    return parseJson(input);
  }
  if (operation === 'format') {
    return formatJsonSorted(input, indent);
  }
  if (operation === 'query') {
    return queryJson(input, query);
  }
  throw new Error(`Invalid operation '${operation}'. Must be 'parse', 'format', or 'query'.`);
}
