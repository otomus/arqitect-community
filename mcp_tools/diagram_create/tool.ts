/**
 * Create diagrams from text definitions and save as SVG.
 */

import * as fs from 'fs';
import * as path from 'path';

const SUPPORTED_DIAGRAM_TYPES = ['flowchart', 'sequence', 'class'] as const;
type DiagramType = typeof SUPPORTED_DIAGRAM_TYPES[number];

/**
 * Escape special XML characters in a string.
 *
 * @param text - Raw text
 * @returns XML-safe text
 */
function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Wrap SVG content with the root element and arrowhead marker definition.
 *
 * @param width - SVG width
 * @param height - SVG height
 * @param content - Inner SVG elements
 * @returns Complete SVG document string
 */
function wrapSvg(width: number, height: number, content: string): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" ` +
    `width="${width}" height="${height}" ` +
    `viewBox="0 0 ${width} ${height}">\n` +
    `  <defs>\n` +
    `    <marker id="arrowhead" markerWidth="10" markerHeight="7" ` +
    `refX="10" refY="3.5" orient="auto">\n` +
    `      <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>\n` +
    `    </marker>\n` +
    `  </defs>\n` +
    `${content}\n` +
    `</svg>`
  );
}

/**
 * Extract node names from 'A -> B -> C' style syntax.
 *
 * @param definition - Flowchart definition string
 * @returns Array of node names
 */
function parseFlowchartNodes(definition: string): string[] {
  return definition.split(/\s*->\s*/).filter((node) => node.trim()).map((node) => node.trim());
}

/**
 * Extract unique participant names from sequence diagram lines.
 *
 * @param lines - Array of sequence definition lines
 * @returns Ordered array of unique participant names
 */
function extractSequenceParticipants(lines: string[]): string[] {
  const participants: string[] = [];
  for (const line of lines) {
    const match = line.match(/^(\w+)\s*->\s*(\w+)/);
    if (match) {
      for (const name of [match[1], match[2]]) {
        if (!participants.includes(name)) {
          participants.push(name);
        }
      }
    }
  }
  return participants;
}

/**
 * Generate a flowchart SVG from 'A -> B -> C' style definitions.
 *
 * @param definition - Flowchart definition
 * @returns SVG string
 */
function generateFlowchartSvg(definition: string): string {
  const nodes = parseFlowchartNodes(definition);
  const boxWidth = 120;
  const boxHeight = 40;
  const marginY = 30;
  const padding = 20;

  const totalHeight = nodes.length * (boxHeight + marginY) + padding;
  const svgWidth = boxWidth + padding * 2;
  const centerX = Math.floor(svgWidth / 2);

  const elements: string[] = [];
  for (let i = 0; i < nodes.length; i++) {
    const y = padding + i * (boxHeight + marginY);
    const x = centerX - Math.floor(boxWidth / 2);
    elements.push(
      `  <rect x="${x}" y="${y}" width="${boxWidth}" ` +
      `height="${boxHeight}" rx="5" ry="5" ` +
      `fill="#4A90D9" stroke="#2C5F8A" stroke-width="1.5"/>`
    );
    const textY = y + Math.floor(boxHeight / 2) + 5;
    elements.push(
      `  <text x="${centerX}" y="${textY}" ` +
      `text-anchor="middle" fill="white" ` +
      `font-family="Arial" font-size="14">${escapeXml(nodes[i])}</text>`
    );
    if (i < nodes.length - 1) {
      const arrowYStart = y + boxHeight;
      const arrowYEnd = y + boxHeight + marginY;
      elements.push(
        `  <line x1="${centerX}" y1="${arrowYStart}" ` +
        `x2="${centerX}" y2="${arrowYEnd}" ` +
        `stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>`
      );
    }
  }

  return wrapSvg(svgWidth, totalHeight, elements.join('\n'));
}

/**
 * Generate a sequence diagram SVG from 'A -> B: message' lines.
 *
 * @param definition - Sequence diagram definition
 * @returns SVG string
 */
function generateSequenceSvg(definition: string): string {
  const lines = definition.trim().split('\n').map((l) => l.trim()).filter(Boolean);
  const participants = extractSequenceParticipants(lines);
  const spacing = 160;
  const svgWidth = participants.length * spacing + 40;
  const headerY = 30;
  const rowHeight = 50;

  const elements: string[] = [];
  for (let i = 0; i < participants.length; i++) {
    const x = 40 + i * spacing;
    elements.push(
      `  <rect x="${x - 40}" y="${headerY - 15}" width="80" ` +
      `height="30" rx="3" fill="#4A90D9" stroke="#2C5F8A"/>`
    );
    elements.push(
      `  <text x="${x}" y="${headerY + 5}" text-anchor="middle" ` +
      `fill="white" font-family="Arial" font-size="12">` +
      `${escapeXml(participants[i])}</text>`
    );
    const lineTop = headerY + 15;
    const lineBottom = headerY + 15 + lines.length * rowHeight + 20;
    elements.push(
      `  <line x1="${x}" y1="${lineTop}" x2="${x}" y2="${lineBottom}" ` +
      `stroke="#999" stroke-width="1" stroke-dasharray="4,4"/>`
    );
  }

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(/^(\w+)\s*->\s*(\w+)\s*:\s*(.*)/);
    if (!match) continue;
    const [, src, dst, msg] = match;
    if (!participants.includes(src) || !participants.includes(dst)) continue;
    const srcX = 40 + participants.indexOf(src) * spacing;
    const dstX = 40 + participants.indexOf(dst) * spacing;
    const y = headerY + 40 + i * rowHeight;
    elements.push(
      `  <line x1="${srcX}" y1="${y}" x2="${dstX}" y2="${y}" ` +
      `stroke="#333" stroke-width="1.5" marker-end="url(#arrowhead)"/>`
    );
    const midX = Math.floor((srcX + dstX) / 2);
    elements.push(
      `  <text x="${midX}" y="${y - 8}" text-anchor="middle" ` +
      `font-family="Arial" font-size="11" fill="#333">` +
      `${escapeXml(msg)}</text>`
    );
  }

  const totalHeight = headerY + 15 + lines.length * rowHeight + 40;
  return wrapSvg(svgWidth, totalHeight, elements.join('\n'));
}

/**
 * Generate a class diagram SVG from 'ClassName: method1, method2' lines.
 *
 * @param definition - Class diagram definition
 * @returns SVG string
 */
function generateClassSvg(definition: string): string {
  const lines = definition.trim().split('\n').map((l) => l.trim()).filter(Boolean);
  const boxWidth = 180;
  const margin = 20;
  let yOffset = 20;

  const elements: string[] = [];
  for (const line of lines) {
    const parts = line.split(':', 2);
    const className = parts[0].trim();
    const methods = parts.length > 1
      ? parts[1].split(',').map((m) => m.trim())
      : [];

    const headerHeight = 30;
    const methodHeight = 20 * Math.max(methods.length, 1);
    const boxHeight = headerHeight + methodHeight + 10;

    elements.push(
      `  <rect x="${margin}" y="${yOffset}" width="${boxWidth}" ` +
      `height="${boxHeight}" fill="white" stroke="#333" stroke-width="1.5"/>`
    );
    elements.push(
      `  <rect x="${margin}" y="${yOffset}" width="${boxWidth}" ` +
      `height="${headerHeight}" fill="#4A90D9" stroke="#333" stroke-width="1.5"/>`
    );
    elements.push(
      `  <text x="${margin + Math.floor(boxWidth / 2)}" y="${yOffset + 20}" ` +
      `text-anchor="middle" fill="white" font-family="Arial" ` +
      `font-size="13" font-weight="bold">${escapeXml(className)}</text>`
    );
    for (let j = 0; j < methods.length; j++) {
      const methodY = yOffset + headerHeight + 18 + j * 20;
      elements.push(
        `  <text x="${margin + 10}" y="${methodY}" ` +
        `font-family="Arial" font-size="11" fill="#333">` +
        `${escapeXml(methods[j])}</text>`
      );
    }

    yOffset += boxHeight + margin;
  }

  const totalHeight = yOffset + margin;
  const svgWidth = boxWidth + margin * 2;
  return wrapSvg(svgWidth, totalHeight, elements.join('\n'));
}

/**
 * Generate SVG content based on diagram type and definition.
 *
 * @param diagramType - Type of diagram (flowchart, sequence, class)
 * @param definition - Text definition for the diagram
 * @returns SVG string
 * @throws Error if diagram type is unknown
 */
function generateSvg(diagramType: DiagramType, definition: string): string {
  if (diagramType === 'flowchart') return generateFlowchartSvg(definition);
  if (diagramType === 'sequence') return generateSequenceSvg(definition);
  if (diagramType === 'class') return generateClassSvg(definition);
  throw new Error(`Unknown diagram type: ${diagramType}`);
}

/**
 * Create a diagram from a text definition and save it to a file.
 *
 * @param diagramType - Type of diagram (flowchart, sequence, class)
 * @param definition - Text definition describing the diagram structure
 * @param outputPath - File path for the output image (.svg or .png)
 * @returns Confirmation message with the output path
 * @throws Error if diagram_type is unsupported or definition is empty
 */
export function run(diagramType: string, definition: string, outputPath: string): string {
  if (!SUPPORTED_DIAGRAM_TYPES.includes(diagramType as DiagramType)) {
    throw new Error(
      `Unsupported diagram type: ${diagramType}. ` +
      `Supported types: ${SUPPORTED_DIAGRAM_TYPES.join(', ')}`
    );
  }

  if (!definition.trim()) {
    throw new Error('Diagram definition cannot be empty');
  }

  const svgContent = generateSvg(diagramType as DiagramType, definition);

  const outputDir = path.dirname(outputPath);
  if (outputDir) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  if (outputPath.endsWith('.png')) {
    // PNG conversion not supported in TypeScript version; save as SVG fallback
    const svgPath = outputPath.replace(/\.png$/, '.svg');
    fs.writeFileSync(svgPath, svgContent, 'utf-8');
    return (
      `error: PNG output requires a native SVG-to-PNG library. SVG saved to ${svgPath} instead.`
    );
  }

  fs.writeFileSync(outputPath, svgContent, 'utf-8');
  return `Diagram saved to ${outputPath}`;
}
