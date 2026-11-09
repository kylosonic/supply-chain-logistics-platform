#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const { downloadArtifact } = require('@electron/get');
const yauzl = require('yauzl');
const { safeArchivePath } = require('./archive-path.cjs');

const checkOnly = process.argv.includes('--check');
const MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024;
const MAX_SYMLINK_BYTES = 4096;

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

function openZip(zipPath) {
  return new Promise((resolve, reject) => {
    yauzl.open(zipPath, { lazyEntries: true, autoClose: true }, (error, archive) => {
      if (error) reject(error);
      else resolve(archive);
    });
  });
}

function openEntryStream(archive, entry) {
  return new Promise((resolve, reject) => {
    archive.openReadStream(entry, (error, stream) => {
      if (error) reject(error);
      else resolve(stream);
    });
  });
}

async function readSmallEntry(archive, entry) {
  if (entry.uncompressedSize > MAX_SYMLINK_BYTES) {
    throw new Error(`[desktop] Symlink target is unexpectedly large: ${entry.fileName}`);
  }
  const stream = await openEntryStream(archive, entry);
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

async function extractArchive(zipPath, destination) {
  const archive = await openZip(zipPath);
  let extractedBytes = 0;

  await new Promise((resolve, reject) => {
    let settled = false;
    const fail = (error) => {
      if (settled) return;
      settled = true;
      archive.close();
      reject(error);
    };

    archive.on('error', fail);
    archive.on('end', () => {
      if (settled) return;
      settled = true;
      resolve();
    });
    archive.on('entry', async (entry) => {
      try {
        const targetPath = safeArchivePath(destination, entry.fileName);
        const mode = entry.externalFileAttributes >>> 16;
        const isDirectory = entry.fileName.endsWith('/');
        const isSymlink = (mode & 0o170000) === 0o120000;

        if (isDirectory) {
          fs.mkdirSync(targetPath, { recursive: true });
        } else if (isSymlink) {
          const linkTarget = (await readSmallEntry(archive, entry)).trim();
          const resolvedTarget = path.resolve(path.dirname(targetPath), linkTarget);
          const relativeTarget = path.relative(destination, resolvedTarget);
          if (
            path.isAbsolute(linkTarget) ||
            relativeTarget.startsWith('..') ||
            path.isAbsolute(relativeTarget)
          ) {
            throw new Error(`[desktop] Unsafe symlink in Electron archive: ${entry.fileName}`);
          }
          fs.mkdirSync(path.dirname(targetPath), { recursive: true });
          fs.rmSync(targetPath, { force: true });
          fs.symlinkSync(linkTarget, targetPath);
        } else {
          fs.mkdirSync(path.dirname(targetPath), { recursive: true });
          const stream = await openEntryStream(archive, entry);
          const output = fs.createWriteStream(targetPath);
          await new Promise((streamResolve, streamReject) => {
            stream.on('data', (chunk) => {
              extractedBytes += chunk.length;
              if (extractedBytes > MAX_ARCHIVE_BYTES) {
                stream.destroy();
                output.destroy();
                streamReject(new Error('[desktop] Electron archive exceeds the extraction limit'));
              }
            });
            stream.on('error', streamReject);
            output.on('error', streamReject);
            output.on('finish', streamResolve);
            stream.pipe(output);
          });
          if (process.platform !== 'win32' && mode) fs.chmodSync(targetPath, mode & 0o777);
        }
        archive.readEntry();
      } catch (error) {
        fail(error);
      }
    });
    archive.readEntry();
  });
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
  await extractArchive(zipPath, distDir);

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
