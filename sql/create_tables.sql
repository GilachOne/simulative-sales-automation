CREATE TABLE IF NOT EXISTS sales (
    shop_num INTEGER NOT NULL CHECK (shop_num > 0),
    cash_num INTEGER NOT NULL CHECK (cash_num > 0),
    doc_id TEXT NOT NULL,
    line_num INTEGER NOT NULL CHECK (line_num > 0),
    item TEXT NOT NULL,
    category TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    discount NUMERIC(12, 2) NOT NULL CHECK (discount >= 0 AND discount <= amount * price),
    PRIMARY KEY (shop_num, cash_num, doc_id, line_num)
);

CREATE TABLE IF NOT EXISTS loaded_files (
    filename TEXT NOT NULL,
    sha256 CHAR(64) NOT NULL,
    row_count INTEGER NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (filename, sha256)
);
