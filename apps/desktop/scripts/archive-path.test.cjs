const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');

const { safeArchivePath } = require('./archive-path.cjs');

const root = path.resolve('extract-root');

test('resolves nested archive paths inside the destination', () => {
  assert.equal(safeArchivePath(root, 'electron.exe'), path.join(root, 'electron.exe'));
  assert.equal(
    safeArchivePath(root, 'resources/app.asar'),
    path.join(root, 'resources', 'app.asar'),
  );
});

test('rejects absolute and parent-traversing archive paths', () => {
  assert.throws(() => safeArchivePath(root, '../outside'));
  assert.throws(() => safeArchivePath(root, 'folder/../../outside'));
  assert.throws(() => safeArchivePath(root, '/absolute'));
  assert.throws(() => safeArchivePath(root, 'C:\\absolute'));
});
