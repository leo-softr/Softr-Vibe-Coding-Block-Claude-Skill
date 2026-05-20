#!/usr/bin/env node

var fs = require('fs');
var path = require('path');
var os = require('os');

var SKILL_NAME = 'softr-vibe-coding';
var SKILL_DIR = path.join(os.homedir(), '.claude', 'skills', SKILL_NAME);
var SETTINGS_FILE = path.join(os.homedir(), '.claude', 'settings.json');
var PACKAGE_ROOT = path.resolve(__dirname, '..');

var SKILL_FILES = ['SKILL.md', 'ui-ux-guidelines.md', 'README.md', 'LICENSE'];
var SKILL_DIRS = ['references', 'datasources'];

var HOOK_COMMAND = 'npx -y --prefer-online ' + SKILL_NAME + '@latest sync';

function log(msg) {
  console.log('[' + SKILL_NAME + '] ' + msg);
}

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  var stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    var entries = fs.readdirSync(src);
    for (var i = 0; i < entries.length; i++) {
      copyRecursive(path.join(src, entries[i]), path.join(dest, entries[i]));
    }
  } else {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

function syncSkillFiles() {
  fs.mkdirSync(SKILL_DIR, { recursive: true });

  for (var i = 0; i < SKILL_FILES.length; i++) {
    var src = path.join(PACKAGE_ROOT, SKILL_FILES[i]);
    if (fs.existsSync(src)) {
      copyRecursive(src, path.join(SKILL_DIR, SKILL_FILES[i]));
    }
  }

  for (var j = 0; j < SKILL_DIRS.length; j++) {
    var srcDir = path.join(PACKAGE_ROOT, SKILL_DIRS[j]);
    var destDir = path.join(SKILL_DIR, SKILL_DIRS[j]);
    if (fs.existsSync(srcDir)) {
      // Wipe destination first so files removed upstream are also removed locally.
      if (fs.existsSync(destDir)) {
        fs.rmSync(destDir, { recursive: true, force: true });
      }
      copyRecursive(srcDir, destDir);
    }
  }
}

function readSettings() {
  if (!fs.existsSync(SETTINGS_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
  } catch (e) {
    console.error('[' + SKILL_NAME + '] ERROR: could not parse ' + SETTINGS_FILE + ': ' + e.message);
    process.exit(1);
  }
}

function writeSettings(settings) {
  fs.mkdirSync(path.dirname(SETTINGS_FILE), { recursive: true });
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2) + '\n');
}

function hookExists(settings) {
  var sessionStart = (settings.hooks && settings.hooks.SessionStart) || [];
  for (var i = 0; i < sessionStart.length; i++) {
    var hooks = sessionStart[i].hooks || [];
    for (var j = 0; j < hooks.length; j++) {
      var h = hooks[j];
      if (h.type === 'command' && typeof h.command === 'string' && h.command.indexOf(SKILL_NAME) !== -1) {
        return true;
      }
    }
  }
  return false;
}

function installHook() {
  var settings = readSettings();

  if (!settings.hooks) settings.hooks = {};
  if (!settings.hooks.SessionStart) settings.hooks.SessionStart = [];

  if (hookExists(settings)) {
    log('SessionStart hook already configured — leaving as is.');
    return;
  }

  settings.hooks.SessionStart.push({
    hooks: [{ type: 'command', command: HOOK_COMMAND }]
  });

  writeSettings(settings);
  log('Added SessionStart hook to ' + SETTINGS_FILE);
}

function cmdInit() {
  log('Installing skill to ' + SKILL_DIR);
  syncSkillFiles();
  log('Skill files installed.');
  installHook();
  log('Done. Start a new Claude Code session to load the skill.');
}

function cmdSync() {
  syncSkillFiles();
}

function cmdHelp() {
  console.log('Usage: npx ' + SKILL_NAME + '@latest <command>');
  console.log('');
  console.log('Commands:');
  console.log('  init   First-time install. Copies skill into ~/.claude/skills/' + SKILL_NAME + '/');
  console.log('         and adds a SessionStart hook to auto-update on each Claude Code session.');
  console.log('  sync   Refresh skill files (called by the SessionStart hook).');
  console.log('  help   Show this message.');
}

var cmd = process.argv[2];
if (cmd === 'init') {
  cmdInit();
} else if (cmd === 'sync') {
  cmdSync();
} else if (cmd === 'help' || cmd === '--help' || cmd === '-h' || cmd === undefined) {
  cmdHelp();
} else {
  console.error('[' + SKILL_NAME + '] Unknown command: ' + cmd);
  cmdHelp();
  process.exit(1);
}
