const fs = require('fs');
const path = require('path');

const envPath = path.resolve(__dirname, '../.env');
const fallbackPath = path.resolve(__dirname, '../.env.example');
const source = fs.existsSync(envPath) ? envPath : fallbackPath;

const vars = {};
fs.readFileSync(source, 'utf8').split('\n').forEach(line => {
  const [key, val] = line.split('=');
  if (key && val) vars[key.trim()] = val.trim();
});

const apiUrl = vars['API_URL'] || 'http://localhost:8000';

const dev = `export const environment = {\n  production: false,\n  apiUrl: '${apiUrl}',\n};\n`;
const prod = `export const environment = {\n  production: true,\n  apiUrl: '${apiUrl}',\n};\n`;

fs.writeFileSync(path.resolve(__dirname, '../src/environments/environment.development.ts'), dev);
fs.writeFileSync(path.resolve(__dirname, '../src/environments/environment.ts'), prod);

console.log(`[set-env] API_URL=${apiUrl}`);
