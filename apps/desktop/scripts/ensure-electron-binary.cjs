#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const childProcess = require('child_process');
const extract = require('extract-zip');
const { downloadArtifact } = require('@electron/get');

const checkOnly = process.argv.includes('--check');

const electronRoot = path.resolve(__dirname, '..', 'node_modules', 'electron');
const electronPackageJson = path.join(electronRoot, 'package.json');
const checksumsPath = path.join(electronRoot, 'checksums.json');
const distDir = path.join(electronRoot, 'dist');
const versionFile = path.join(distDir, 'version');
const pathFile = path.join(electronRoot, 'path.txt');

function platformBinaryPath(platform) {
  switch (platform) {
    case 'darwin':
    case 'mas':
      return 'Electron.app/Contents/MacOS/Electron';
    case 'linux':
    case 'freebsd':
    case 'openbsd':
      return 'electron';
    case 'win32':
      return 'electron.exe';
    default:
      throw new Error(`[desktop] Unsupported platform for Electron binary: ${platform}`);
  }
}

function resolvePlatform() {
  return process.env.npm_config_platform || os.platform();
}

function resolveArch() {
  return process.env.npm_config_arch || process.arch;
}

function readVersion() {
  if (!fs.existsSync(electronPackageJson)) {
    throw new Error('[desktop] Electron package is not installed. Run npm --prefix apps/desktop install first.');
  }

  const raw = fs.readFileSync(electronPackageJson, 'utf8');
  const parsed = JSON.parse(raw);
  return parsed.version;
}

function isBinaryReady(version, binaryPath) {
  try {
    const installedVersion = fs.readFileSync(versionFile, 'utf8').trim().replace(/^v/, '');
    const configuredPath = fs.readFileSync(pathFile, 'utf8').trim();
    const executablePath = path.join(distDir, binaryPath);

    return installedVersion === version && configuredPath === binaryPath && fs.existsSync(executablePath);
  } catch {
    return false;
  }
}

async function ensureElectronBinary() {
  if (process.env.ELECTRON_SKIP_BINARY_DOWNLOAD) {
    console.log('[desktop] ELECTRON_SKIP_BINARY_DOWNLOAD is set; skipping binary check.');
    return;
  }

  const version = readVersion();
  const platform = resolvePlatform();
  const arch = resolveArch();
  const binaryPath = platformBinaryPath(platform);

  if (isBinaryReady(version, binaryPath)) {
    console.log(`[desktop] Electron ${version} binary is ready (${platform}-${arch}).`);
    return;
  }

  if (checkOnly) {
    throw new Error(`[desktop] Electron ${version} binary is missing for ${platform}-${arch}. Run npm --prefix apps/desktop install to repair.`);
  }

  console.log(`[desktop] Repairing Electron ${version} binary for ${platform}-${arch}...`);
  fs.rmSync(distDir, { recursive: true, force: true });
  fs.mkdirSync(distDir, { recursive: true });

  const checksums = fs.existsSync(checksumsPath) ? require(checksumsPath) : undefined;
  const zipPath = await downloadArtifact({
    version,
    artifactName: 'electron',
    platform,
    arch,
    checksums,
  });

  console.log(`[desktop] Downloaded Electron artifact: ${zipPath}`);

  if (platform === 'win32') {
    // Node 24 + extract-zip can intermittently exit before extraction completes on Windows.
    // Prefer the native tar command for deterministic results.
    childProcess.execFileSync('tar', ['-xf', zipPath, '-C', distDir], { stdio: 'inherit' });
  } else {
    await extract(zipPath, { dir: distDir });
  }

  const sourceTypeFile = path.join(distDir, 'electron.d.ts');
  const targetTypeFile = path.join(electronRoot, 'electron.d.ts');
  if (fs.existsSync(sourceTypeFile)) {
    fs.renameSync(sourceTypeFile, targetTypeFile);
  }

  await fs.promises.writeFile(pathFile, binaryPath, 'utf8');

  if (!isBinaryReady(version, binaryPath)) {
    throw new Error('[desktop] Electron binary repair completed but validation still failed.');
  }

  console.log('[desktop] Electron binary repair complete.');
}

ensureElectronBinary().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
