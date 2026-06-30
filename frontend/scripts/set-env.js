const fs = require('fs');
const path = require('path');

const envPath = path.resolve(__dirname, '../.env');
const fallbackPath = path.resolve(__dirname, '../.env.example');
const source = fs.existsSync(envPath) ? envPath : fallbackPath;

const vars = {};
if (fs.existsSync(source)) {
  fs.readFileSync(source, 'utf8').split('\n').forEach(line => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
      return;
    }

    const separator = trimmed.indexOf('=');
    if (separator === -1) {
      return;
    }

    const key = trimmed.slice(0, separator).trim();
    const val = trimmed.slice(separator + 1).trim();
    if (key && val) {
      vars[key] = val;
    }
  });
}

const apiUrl = process.env.API_URL || vars.API_URL || 'http://localhost:8000';
const safeApiUrl = apiUrl.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
const runtimeEnv = `window.__tccompEnv = window.__tccompEnv || {};\nwindow.__tccompEnv.apiUrl = '${safeApiUrl}';\n`;

fs.writeFileSync(path.resolve(__dirname, '../src/assets/env.js'), runtimeEnv);

console.log(`[set-env] API_URL=${apiUrl}`);
