"""Запуск загрузчика, в том числе с локальной переносимой PostgreSQL."""
import json
import os
import subprocess

from common import ROOT, settings, setup_log
from load import load
import logging


if __name__ == '__main__':
    setup_log('load')
    try:
        runtime_path = ROOT / 'local-runtime.json'
        if runtime_path.exists():
            runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
            pg_ctl = os.path.join(runtime['pg_bin'], 'pg_ctl.exe')
            command = [pg_ctl, '-D', runtime['pg_data']]
            status = subprocess.run(command + ['status'], capture_output=True)
            if status.returncode != 0:
                subprocess.run(command + ['-l', str(ROOT / '.local' / 'server.log'),
                               '-o', '-h 127.0.0.1 -p 55440', '-w', 'start'], check=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            os.environ['PGPASSWORD'] = (ROOT / '.local' / 'db-password.txt').read_text().strip()
        raise SystemExit(1 if load(settings()) else 0)
    except Exception as error:
        logging.error('Ошибка запуска загрузчика: %s', type(error).__name__)
        raise SystemExit(1)
