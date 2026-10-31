-- PostgreSQL schema for Delivery - On The Go assessment.
-- Load the eight CSV files from the data/ directory using the \copy commands in import_data.sql.

CREATE TABLE IF NOT EXISTS hubs (
    hub_id TEXT PRIMARY KEY,
    hub_name TEXT NOT NULL,
    cluster TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    hub_id TEXT NOT NULL REFERENCES hubs(hub_id),
    salary_type TEXT NOT NULL,
    joining_date DATE NOT NULL,
    active_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    hub_id TEXT NOT NULL REFERENCES hubs(hub_id),
    created_at TIMESTAMP NOT NULL,
    final_status TEXT NOT NULL,
    cod_amount NUMERIC(12,2) NOT NULL,
    delivery_charge NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_logs (
    log_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    status TEXT NOT NULL,
    hold_reason TEXT,
    event_time TIMESTAMP NOT NULL,
    attempt_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_salary (
    salary_type TEXT PRIMARY KEY,
    monthly_salary NUMERIC(12,2) NOT NULL,
    daily_allowance NUMERIC(12,2) NOT NULL,
    allowance_per_delivery NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS costs (
    what TEXT PRIMARY KEY,
    amount_bdt NUMERIC(12,2) NOT NULL,
    when_charged TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rules (
    rule TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS volume_forecast (
    hub_id TEXT NOT NULL REFERENCES hubs(hub_id),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    expected_orders INTEGER NOT NULL,
    PRIMARY KEY (hub_id, week_start)
);
