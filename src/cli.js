#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

import { convertAntdFormToHtml } from './index.js';

async function main() {
  const { positional, options } = parseArgs(process.argv.slice(2));

  if (options.help || positional.length === 0) {
    printUsage();
    process.exit(options.help ? 0 : 1);
  }

  if (positional.length > 1) {
    console.error('Unexpected argument:', positional.slice(1).join(' '));
    printUsage();
    process.exit(1);
  }

  const inputPath = positional[0];
  const outputPath = options.out || null;

  let rawInput;
  try {
    rawInput = inputPath === '-'
      ? await readStdin()
      : fs.readFileSync(resolveRelative(inputPath), 'utf8');
  } catch (error) {
    console.error(`Failed to read input "${inputPath}":`, error.message);
    process.exit(1);
  }

  let definition;
  try {
    definition = JSON.parse(rawInput);
  } catch (error) {
    console.error('Input is not valid JSON:', error.message);
    process.exit(1);
  }

  const htmlOptions = {
    title: options.title,
    includeStyles: options.includeStyles,
    styles: options.styles
  };

  try {
    const html = convertAntdFormToHtml(definition, { html: htmlOptions });
    if (outputPath) {
      const targetPath = resolveRelative(outputPath);
      ensureParentDirectory(targetPath);
      fs.writeFileSync(targetPath, html, 'utf8');
    } else {
      process.stdout.write(html);
    }
  } catch (error) {
    const details = Array.isArray(error.details) && error.details.length > 0
      ? `\n- ${error.details.join('\n- ')}`
      : '';
    console.error(`Failed to convert form definition: ${error.message}${details}`);
    process.exit(1);
  }
}

function parseArgs(argv) {
  const positional = [];
  const options = {
    includeStyles: true
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case '-h':
      case '--help':
        options.help = true;
        break;
      case '-o':
      case '--out':
        options.out = requireValue(argv, ++i, arg);
        break;
      case '--title':
        options.title = requireValue(argv, ++i, arg);
        break;
      case '--no-styles':
        options.includeStyles = false;
        break;
      case '--styles':
        options.styles = readStyles(requireValue(argv, ++i, arg));
        options.includeStyles = true;
        break;
      default:
        if (arg.startsWith('-')) {
          console.error(`Unknown option: ${arg}`);
          options.help = true;
          break;
        }
        positional.push(arg);
    }
  }

  return { positional, options };
}

function requireValue(argv, index, flag) {
  const value = argv[index];
  if (!value || value.startsWith('-')) {
    console.error(`Option ${flag} requires a value.`);
    process.exit(1);
  }
  return value;
}

function readStyles(relativePath) {
  try {
    return fs.readFileSync(resolveRelative(relativePath), 'utf8');
  } catch (error) {
    console.error(`Failed to read styles from "${relativePath}":`, error.message);
    process.exit(1);
  }
}

function resolveRelative(targetPath) {
  if (!targetPath) return targetPath;
  if (path.isAbsolute(targetPath)) {
    return targetPath;
  }
  return path.resolve(process.cwd(), targetPath);
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString('utf8');
}

function printUsage() {
  console.log(`Usage: antd-to-html <form.json> [options]

Options:
  -o, --out <file>      Write HTML output to file (default: stdout)
      --title <text>    Override the document title
      --no-styles       Omit inline styles in the HTML output
      --styles <file>   Inject custom CSS instead of the default theme
  -h, --help            Display this help message

Use '-' as the input path to read the form JSON from stdin.`);
}

function ensureParentDirectory(filePath) {
  const directory = path.dirname(filePath);
  if (!directory || directory === '.' || directory === '/') {
    return;
  }
  fs.mkdirSync(directory, { recursive: true });
}

await main();
