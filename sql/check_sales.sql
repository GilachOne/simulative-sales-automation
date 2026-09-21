SELECT COUNT(*) AS rows, COUNT(DISTINCT (shop_num, cash_num, doc_id)) AS receipts,
       SUM(amount * price - discount) AS revenue
FROM sales;

SELECT shop_num, cash_num, COUNT(*) AS rows, SUM(amount * price - discount) AS revenue
FROM sales GROUP BY shop_num, cash_num ORDER BY shop_num, cash_num;

SELECT filename, row_count, loaded_at FROM loaded_files ORDER BY loaded_at;
