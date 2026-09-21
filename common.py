import json
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ['doc_id', 'item', 'category', 'amount', 'price', 'discount']


def settings():
    with open(ROOT / 'config.json', encoding='utf-8-sig') as file:
        config = json.load(file)
    for key in ('shops', 'cash_registers_per_shop', 'receipts_per_cash'):
        if type(config.get(key)) is not int or config[key] < 1:
            raise ValueError(f'{key}: нужно положительное целое число')
    if not isinstance(config.get('database'), dict):
        raise ValueError('Нет настроек database')
    for key in ('host', 'port', 'dbname', 'user'):
        if key not in config['database']:
            raise ValueError(f'Нет настройки database.{key}')
    if os.getenv('PGPASSWORD'):
        config['database']['password'] = os.environ['PGPASSWORD']
    return config


def setup_log(name):
    (ROOT / 'logs').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.FileHandler(ROOT / 'logs' / f'{name}.log', encoding='utf-8'),
                                  logging.StreamHandler()])
