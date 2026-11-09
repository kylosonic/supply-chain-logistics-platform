const path = require('path');

function safeArchivePath(root, entryName) {
  const normalized = entryName.replaceAll('\\', '/');
  const segments = normalized.split('/').filter(Boolean);
  if (
    normalized.startsWith('/') ||
    /^[A-Za-z]:/.test(normalized) ||
    segments.some((segment) => segment === '..')
  ) {
    throw new Error(`Unsafe path in Electron archive: ${entryName}`);
  }
  const destination = path.resolve(root, ...segments);
  const relative = path.relative(root, destination);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`Archive entry escapes the destination: ${entryName}`);
  }
  return destination;
}

module.exports = { safeArchivePath };
