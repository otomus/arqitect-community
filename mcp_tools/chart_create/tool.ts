/**
 * Create chart images from JSON data using chart.js with chartjs-node-canvas.
 */

import * as fs from 'fs';
import * as path from 'path';
import { ChartJSNodeCanvas } from 'chartjs-node-canvas';

const SUPPORTED_CHART_TYPES = ['bar', 'line', 'pie', 'scatter'] as const;
type ChartType = typeof SUPPORTED_CHART_TYPES[number];

interface ChartData {
  labels: string[];
  values: number[];
}

/**
 * Parse and validate the JSON chart data.
 *
 * @param data - JSON string containing labels and values
 * @returns Parsed chart data with labels and values
 * @throws Error if data is invalid JSON or missing required fields
 */
function parseChartData(data: string): ChartData {
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(data) as Record<string, unknown>;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Invalid JSON data: ${msg}`);
  }

  if (!('labels' in parsed) || !('values' in parsed)) {
    throw new Error("Data must contain 'labels' and 'values' keys");
  }

  const labels = parsed['labels'] as string[];
  const values = parsed['values'] as number[];

  if (labels.length !== values.length) {
    throw new Error('Labels and values must have the same length');
  }

  return { labels, values };
}

/**
 * Create a chart image and save it to the specified path.
 *
 * @param chartType - Type of chart (bar, line, pie, scatter)
 * @param data - JSON string containing labels and values
 * @param outputPath - File path for the output image
 * @param title - Optional chart title
 * @returns Confirmation message with the output path
 * @throws Error if chart type is unsupported or data is malformed
 */
export async function run(
  chartType: string,
  data: string,
  outputPath: string,
  title: string = ''
): Promise<string> {
  if (!SUPPORTED_CHART_TYPES.includes(chartType as ChartType)) {
    throw new Error(
      `Unsupported chart type: ${chartType}. ` +
      `Supported types: ${SUPPORTED_CHART_TYPES.join(', ')}`
    );
  }

  const chartData = parseChartData(data);
  const { labels, values } = chartData;

  const width = 800;
  const height = 600;
  const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height });

  const type = chartType as ChartType;

  const configuration = {
    type: type === 'scatter' ? 'scatter' as const : type as 'bar' | 'line' | 'pie',
    data: {
      labels,
      datasets: [
        {
          label: title || 'Data',
          data: type === 'scatter'
            ? labels.map((label, i) => ({ x: i, y: values[i] }))
            : values,
          backgroundColor: type === 'pie'
            ? labels.map((_, i) => `hsl(${(i * 360) / labels.length}, 70%, 60%)`)
            : 'rgba(74, 144, 217, 0.7)',
          borderColor: 'rgba(44, 95, 138, 1)',
          borderWidth: 1,
          ...(type === 'line' ? { fill: false, pointRadius: 5 } : {}),
        },
      ],
    },
    options: {
      plugins: {
        title: title
          ? { display: true, text: title }
          : { display: false },
      },
    },
  };

  const buffer = await chartJSNodeCanvas.renderToBuffer(configuration as Parameters<typeof chartJSNodeCanvas.renderToBuffer>[0]);

  const outputDir = path.dirname(outputPath);
  if (outputDir) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, buffer);

  return `Chart saved to ${outputPath}`;
}
