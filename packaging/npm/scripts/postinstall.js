#!/usr/bin/env node
const fs = require('node:fs');
const https = require('node:https');
const os = require('node:os');
const path = require('node:path');
const { execSync } = require('node:child_process');

const pkg = require('../package.json');

if (process.env.AGENT_SKIP_DOWNLOAD) {
  console.log('[agent] AGENT_SKIP_DOWNLOAD set, skipping binary download.');
  process.exit(0);
}

const platformMap = {
  darwin: 'macos',
  linux: 'linux'
};

const archMap = {
  x64: 'x64',
  arm64: 'arm64'
};

const platform = platformMap[os.platform()];
const arch = archMap[os.arch()];

if (!platform || !arch) {
  console.warn(`[agent] No prebuilt binary for ${os.platform()}-${os.arch()}. Using python fallback.`);
  process.exit(0);
}

const version = pkg.version;
const assetName = `agent-${platform}-${arch}.tar.gz`;
const downloadUrl = `https://github.com/YOURORG/agent/releases/download/v${version}/${assetName}`;

const binDir = path.join(__dirname, '..', 'bin');
fs.mkdirSync(binDir, { recursive: true });
const archivePath = path.join(binDir, assetName);

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, response => {
      if (response.statusCode !== 200) {
        reject(new Error(`Unexpected response: ${response.statusCode}`));
        return;
      }
      response.pipe(file);
      file.on('finish', () => file.close(resolve));
    }).on('error', reject);
  });
}

(async () => {
  try {
    console.log(`[agent] Downloading ${downloadUrl}`);
    await download(downloadUrl, archivePath);
    const extractDir = path.join(binDir, 'native');
    fs.mkdirSync(extractDir, { recursive: true });
    execSync(`tar -xzf ${archivePath} -C ${extractDir}`);
    const binaryPath = path.join(extractDir, 'agent');
    if (!fs.existsSync(binaryPath)) {
      throw new Error('Extracted archive does not contain agent binary.');
    }
    fs.copyFileSync(binaryPath, path.join(binDir, 'agent-native'));
    fs.chmodSync(path.join(binDir, 'agent-native'), 0o755);
    fs.rmSync(archivePath, { force: true });
    console.log('[agent] Binary installed.');
  } catch (err) {
    console.warn(`[agent] Failed to install prebuilt binary: ${err.message}`);
    console.warn('[agent] Falling back to python module execution.');
  }
})();
