"""Проверка CSV и загрузка в PostgreSQL. Посторонние файлы игнорируются."""
import csv
import hashlib
import io
import logging
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation

import psycopg2
from common import ROOT, FIELDS, settings, setup_log

FILENAME = re.compile(r'([1-9][0-9]*)_([1-9][0-9]*)\.csv')


def read_rows(raw, shop, cash):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';')
    if reader.fieldnames != FIELDS:
        raise ValueError('Неверные названия или порядок столбцов')
    result = []
    line_numbers = defaultdict(int)
    for number, row in enumerate(reader, 2):
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Неверное число столбцов')
            if not re.fullmatch(r'[A-Za-z0-9]+', row['doc_id']):
                raise ValueError('Неверный doc_id')
            if not row['item'].strip() or not row['category'].strip():
                raise ValueError('Пустой товар или категория')
            amount = int(row['amount'])
            price, discount = Decimal(row['price']), Decimal(row['discount'])
            if not price.is_finite() or not discount.is_finite():
                raise ValueError('Неконечное число')
            if amount <= 0 or price < 0 or not 0 <= discount <= amount * price:
                raise ValueError('Недопустимые количество, цена или скидка')
            if price != price.quantize(Decimal('0.01')) or discount != discount.quantize(Decimal('0.01')):
                raise ValueError('Больше двух знаков после запятой')
            line_numbers[row['doc_id']] += 1
            result.append((shop, cash, row['doc_id'], line_numbers[row['doc_id']],
                           row['item'], row['category'], amount, price, discount))
        except (ValueError, InvalidOperation) as error:
            raise ValueError(f'Строка {number}: {error}') from None
    if not result:
        raise ValueError('В файле нет продаж')
    return result


def load_file(connection, path):
    match = FILENAME.fullmatch(path.name)
    shop, cash = map(int, match.groups())
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    rows = read_rows(raw, shop, cash)
    added = 0
    # Содержимое файла и отметка о его загрузке сохраняются одной транзакцией.
    with connection:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO loaded_files(filename, sha256, row_count) VALUES (%s,%s,%s) '
                           'ON CONFLICT DO NOTHING RETURNING filename', (path.name, checksum, len(rows)))
            if cursor.fetchone() is not None:
                for row in rows:
                    cursor.execute('INSERT INTO sales VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) '
                                   'ON CONFLICT DO NOTHING', row)
                    if cursor.rowcount:
                        added += 1
                    else:
                        cursor.execute('SELECT item,category,amount,price,discount FROM sales '
                                       'WHERE shop_num=%s AND cash_num=%s AND doc_id=%s AND line_num=%s', row[:4])
                        if cursor.fetchone() != row[4:]:
                            raise ValueError('Уже загруженная строка чека изменилась')
    logging.info('%s: прочитано %s, добавлено %s', path.name, len(rows), added)
    archive = ROOT / 'archive'
    archive.mkdir(exist_ok=True)
    destination = archive / f'{path.stem}_{checksum}.csv'
    # Замена допустима: одинаковый SHA означает тот же обработанный файл.
    path.replace(destination)
    return added


def load(config):
    connection = psycopg2.connect(**config['database'], connect_timeout=10)
    errors = 0
    added = 0
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute((ROOT / 'sql' / 'create_tables.sql').read_text(encoding='utf-8'))
        (ROOT / 'data').mkdir(exist_ok=True)
        for path in sorted((ROOT / 'data').iterdir()):
            if not path.is_file() or not FILENAME.fullmatch(path.name):
                logging.info('Посторонний файл пропущен: %s', path.name)
                continue
            try:
                added += load_file(connection, path)
            except Exception as error:
                errors += 1
                logging.error('%s: загрузка не завершена (%s)', path.name, type(error).__name__)
        logging.info('Итого добавлено %s строк, ошибочных файлов %s', added, errors)
        return errors
    finally:
        connection.close()


if __name__ == '__main__':
    setup_log('load')
    try:
        raise SystemExit(1 if load(settings()) else 0)
    except Exception as error:
        logging.error('Загрузка прервана: %s', type(error).__name__)
        raise SystemExit(1)
