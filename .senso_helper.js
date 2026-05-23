const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Read which command to run from args: node senso_helper.js <subcommand...> --json-file <path>
const args = process.argv.slice(2);
const jsonFileIdx = args.indexOf('--json-file');
let jsonArg = null;
let sensoArgs = [];

if (jsonFileIdx !== -1) {
  const jsonFile = args[jsonFileIdx + 1];
  const raw = fs.readFileSync(jsonFile, 'utf8');
  jsonArg = JSON.stringify(JSON.parse(raw)); // compact single line
  sensoArgs = [...args.slice(0, jsonFileIdx), '--data', jsonArg, ...args.slice(jsonFileIdx + 2)];
} else {
  sensoArgs = args;
}

// Find senso.cmd
const sensoCmd = path.join(
  process.env.APPDATA || '',
  'npm', 'senso.cmd'
);

const result = spawnSync(sensoCmd, sensoArgs, {
  env: { ...process.env, SENSO_API_KEY: 'tgr_1n8NgNQTEo4ig1Y_4OS6nyuIPyU5xTFGmV6ScykQCPc' },
  encoding: 'utf8',
  shell: false,
  windowsVerbatimArguments: true
});

if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
process.exit(result.status || 0);
