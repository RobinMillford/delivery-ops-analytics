-- Run from the project root in psql after creating the schema.
-- Example: psql "$DATABASE_URL" -f sql/schema.sql
-- Then run this file. Adjust the path if your local folder differs.

\copy hubs FROM 'data/hubs.csv' WITH (FORMAT csv, HEADER true)
\copy agents FROM 'data/agents.csv' WITH (FORMAT csv, HEADER true)
\copy orders FROM 'data/orders.csv' WITH (FORMAT csv, HEADER true)
\copy order_logs FROM 'data/order_logs.csv' WITH (FORMAT csv, HEADER true)
\copy agent_salary FROM 'data/agent_salary.csv' WITH (FORMAT csv, HEADER true)
\copy costs FROM 'data/costs.csv' WITH (FORMAT csv, HEADER true)
\copy rules FROM 'data/rules.csv' WITH (FORMAT csv, HEADER true)
\copy volume_forecast FROM 'data/volume_forecast.csv' WITH (FORMAT csv, HEADER true)
