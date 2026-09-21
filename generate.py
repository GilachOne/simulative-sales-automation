"""Генерация кассовых выгрузок с понедельника по субботу."""
import csv
import logging
import random
from datetime import date
from decimal import Decimal

from common import ROOT, FIELDS, settings, setup_log

PRODUCTS = [
    ('Средство для посуды', 'Бытовая химия', 159),
    ('Порошок стиральный', 'Бытовая химия', 499),
    ('Полотенце', 'Текстиль', 349),
    ('Наволочка', 'Текстиль', 249),
    ('Кружка', 'Посуда', 199),
    ('Тарелка', 'Посуда', 299),
    ('Лопатка кухонная', 'Кухонные принадлежности', 179),
    ('Контейнер', 'Кухонные принадлежности', 229),
]


def generate(config, day=None):
    day = day or date.today()
    if day.weekday() == 6:
        logging.info('Воскресенье: генерация не требуется')
        return 0
    folder = ROOT / 'data'
    folder.mkdir(exist_ok=True)
    created = 0
    for shop in range(1, config['shops'] + 1):
        for cash in range(1, config['cash_registers_per_shop'] + 1):
            path = folder / f'{shop}_{cash}.csv'
            if path.exists():
                # Не перезаписываем выгрузку, которую ещё не забрал загрузчик.
                raise FileExistsError(f'Сначала загрузите существующий файл {path.name}')
            rng = random.Random(f'{day}:{shop}:{cash}')
            temporary = path.with_suffix('.tmp')
            with open(temporary, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(FIELDS)
                for receipt in range(1, config['receipts_per_cash'] + 1):
                    doc_id = f'{day:%Y%m%d}S{shop}C{cash}R{receipt}'
                    for item, category, price in rng.sample(PRODUCTS, rng.randint(1, 4)):
                        amount = rng.randint(1, 3)
                        discount = Decimal(amount * price) * Decimal(rng.choice(['0', '0.05', '0.10']))
                        writer.writerow([doc_id, item, category, amount, f'{price:.2f}', f'{discount:.2f}'])
            temporary.replace(path)
            created += 1
            logging.info('Создан %s', path.name)
    return created


if __name__ == '__main__':
    setup_log('generate')
    try:
        logging.info('Генерация завершена: файлов %s', generate(settings()))
    except Exception as error:
        logging.error('Ошибка генерации: %s', error)
        raise SystemExit(1)
