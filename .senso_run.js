const { execFileSync } = require('child_process');
const fs = require('fs');

const data = fs.readFileSync('.senso_brand_kit.json', 'utf8').trim();

try {
  const result = execFileSync('senso.cmd', [
    'brand-kit', 'set',
    '--data', data,
    '--output', 'json',
    '--quiet'
  ], {
    env: { ...process.env, SENSO_API_KEY: 'tgr_1n8NgNQTEo4ig1Y_4OS6nyuIPyU5xTFGmV6ScykQCPc' },
    encoding: 'utf8',
    shell: false
  });
  console.log(result);
} catch (e) {
  console.error(e.stdout || e.message);
  process.exit(1);
}
