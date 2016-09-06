import os
import subprocess

import sublime
from sublime_plugin import EventListener, TextCommand

SETTINGS_FILE = 'rustfmt.sublime-settings'
RUSTFMT_BIN = '~/.cargo/bin/rustfmt'


class RustfmtOnSave(EventListener):
    def on_pre_save(self, view):
        if sublime.load_settings(SETTINGS_FILE).get('run_on_save', True):
            view.run_command('rustfmt')


class RustfmtCommand(TextCommand):
    def is_enabled(self):
        fn = self.view.file_name()
        if fn is None:
            return self.view.score_selector(0, 'source.rust') > 0
        return fn.lower()[-3:] == '.rs'

    def run(self, edit):
        self.view.set_status('rustfmt', '')
        region = sublime.Region(0, self.view.size())
        src = self.view.substr(region)
        if not src.strip():
            return

        settings = sublime.load_settings(SETTINGS_FILE)
        command = [os.path.expanduser(settings.get('bin', RUSTFMT_BIN))]
        config_path = settings.get('config_path', '').strip()
        if config_path:
            command += ['--config-path', config_path]

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(src.encode('utf-8'))

        if proc.wait() > 0:
            stderr = stderr.decode('utf-8')
            self.view.set_status(
                'rustfmt',
                'rustfmt: ' + stderr.splitlines()[0][6:],
            )
            print(stderr)
            return

        stdout = stdout.decode('utf-8')
        if stdout == src:
            return

        if not stdout.strip():
            return

        self.view.replace(edit, region, stdout)
