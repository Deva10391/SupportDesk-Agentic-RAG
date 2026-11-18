CREATE TABLE orders (
  order_id TEXT PRIMARY KEY, status TEXT, item TEXT, total NUMERIC(8,2),
  eta DATE, customer_name TEXT, customer_email TEXT
);
CREATE ROLE reader LOGIN PASSWORD 'reader';
GRANT SELECT ON orders TO reader;
