/*
Delivery - On The Go | Data Analyst Technical Assessment
SQL dialect: PostgreSQL

Important interpretation notes:
1) One Assigned event is one attempt; each attempt has one outcome event.
2) Dates in the task are inclusive: Week 1 = 2026-10-13 to 2026-10-19;
   Week 2 = 2026-10-20 to 2026-10-26.
3) Week 1 headcount includes all agents. Inactive agents left at the end of Week 1,
   so Week 2 headcount includes only Active agents.
4) Utilisation = Assigned attempts / (available agents * 40 * 7).
5) Q6 cost allocation is on the event week. A workday is inferred from at least one
   Assigned event for that agent on that date.
*/

-- ============================================================
-- Q1. Daily Agent Productivity
-- A complete roster-date grid is retained; no-assignment days show zeroes.
-- The first 20 rows are obtained with ORDER BY ... LIMIT 20.
-- ============================================================

WITH dates AS (
    SELECT d::date AS work_date
    FROM generate_series(
        DATE '2026-10-13',
        DATE '2026-10-26',
        INTERVAL '1 day'
    ) AS s(d)
),
agent_days AS (
    SELECT
        a.agent_id,
        a.agent_name,
        a.hub_id,
        a.salary_type,
        a.joining_date,
        a.active_status,
        d.work_date
    FROM agents a
    CROSS JOIN dates d
    WHERE a.active_status = 'Active'
       OR (a.active_status = 'Inactive' AND d.work_date <= DATE '2026-10-19')
),
daily_events AS (
    SELECT
        o.hub_id,
        l.agent_id,
        l.event_time::date AS work_date,
        COUNT(*) FILTER (WHERE l.status = 'Assigned') AS assigned_attempts,
        COUNT(*) FILTER (WHERE l.status = 'Delivered') AS delivered_attempts,
        COUNT(*) FILTER (WHERE l.status = 'Hold') AS hold_attempts,
        COUNT(*) FILTER (WHERE l.status = 'Returned') AS returned_attempts
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id, l.agent_id, l.event_time::date
),
q1_daily AS (
    SELECT
        d.work_date,
        d.agent_id,
        d.agent_name,
        d.hub_id,
        d.salary_type,
        d.active_status,
        COALESCE(e.assigned_attempts, 0) AS assigned_attempts,
        COALESCE(e.delivered_attempts, 0) AS delivered_attempts,
        COALESCE(e.hold_attempts, 0) AS hold_attempts,
        COALESCE(e.returned_attempts, 0) AS returned_attempts
    FROM agent_days d
    LEFT JOIN daily_events e
      ON e.agent_id = d.agent_id
     AND e.hub_id = d.hub_id
     AND e.work_date = d.work_date
)
SELECT *
FROM q1_daily
ORDER BY work_date, hub_id, agent_id
LIMIT 20;

-- Q1 full hub summary: deliveries per available agent-day.
WITH dates AS (
    SELECT d::date AS work_date
    FROM generate_series(DATE '2026-10-13', DATE '2026-10-26', INTERVAL '1 day') AS s(d)
),
agent_days AS (
    SELECT a.agent_id, a.hub_id, d.work_date
    FROM agents a
    CROSS JOIN dates d
    WHERE a.active_status = 'Active'
       OR (a.active_status = 'Inactive' AND d.work_date <= DATE '2026-10-19')
),
daily_events AS (
    SELECT
        o.hub_id,
        l.agent_id,
        l.event_time::date AS work_date,
        COUNT(*) FILTER (WHERE l.status = 'Delivered') AS delivered_attempts
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id, l.agent_id, l.event_time::date
)
SELECT
    h.hub_id,
    h.hub_name,
    h.cluster,
    SUM(COALESCE(e.delivered_attempts, 0)) AS delivered_attempts,
    COUNT(*) AS available_agent_days,
    ROUND(
        SUM(COALESCE(e.delivered_attempts, 0))::numeric / NULLIF(COUNT(*), 0),
        2
    ) AS avg_deliveries_per_agent_per_day
FROM agent_days a
JOIN hubs h ON h.hub_id = a.hub_id
LEFT JOIN daily_events e
  ON e.agent_id = a.agent_id
 AND e.hub_id = a.hub_id
 AND e.work_date = a.work_date
GROUP BY h.hub_id, h.hub_name, h.cluster
ORDER BY h.hub_id;

-- ============================================================
-- Q2. Hub Utilisation in Week 1 and Week 2
-- Week 1 includes inactive agents; Week 2 excludes them.
-- ============================================================

WITH headcount AS (
    SELECT
        hub_id,
        COUNT(*) AS week1_agents,
        COUNT(*) FILTER (WHERE active_status = 'Active') AS week2_agents
    FROM agents
    GROUP BY hub_id
),
attempts AS (
    SELECT
        o.hub_id,
        COUNT(*) FILTER (
            WHERE l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-19'
        ) AS week1_attempts,
        COUNT(*) FILTER (
            WHERE l.event_time::date BETWEEN DATE '2026-10-20' AND DATE '2026-10-26'
        ) AS week2_attempts
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.status = 'Assigned'
      AND l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id
)
SELECT
    h.hub_id,
    h.hub_name,
    h.cluster,
    a.week1_attempts,
    a.week2_attempts,
    c.week1_agents,
    c.week2_agents,
    ROUND(a.week1_attempts::numeric / (c.week1_agents * 40 * 7), 4) AS week1_utilisation,
    ROUND(a.week2_attempts::numeric / (c.week2_agents * 40 * 7), 4) AS week2_utilisation,
    ROUND((a.week2_attempts::numeric / (c.week2_agents * 40 * 7)) * 100, 2) > 85
        AS week2_above_85pct_target,
    ROUND((a.week2_attempts::numeric / NULLIF(a.week1_attempts, 0) - 1) * 100, 2)
        AS attempt_change_pct
FROM hubs h
JOIN headcount c ON c.hub_id = h.hub_id
JOIN attempts a ON a.hub_id = h.hub_id
ORDER BY h.hub_id;

-- ============================================================
-- Q3. Week 2 Hold Reasons
-- Agent-side reasons per case notes: Late Dispatch, Not Attempted,
-- Agent Time Shortage. All others are customer-side.
-- ============================================================

WITH week2_holds AS (
    SELECT
        o.hub_id,
        l.hold_reason,
        CASE
            WHEN l.hold_reason IN ('Late Dispatch', 'Not Attempted', 'Agent Time Shortage')
                THEN 'Agent-side'
            ELSE 'Customer-side'
        END AS hold_side
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.status = 'Hold'
      AND l.event_time::date BETWEEN DATE '2026-10-20' AND DATE '2026-10-26'
),
hub_totals AS (
    SELECT
        hub_id,
        COUNT(*) AS total_holds,
        COUNT(*) FILTER (WHERE hold_side = 'Agent-side') AS agent_side_holds
    FROM week2_holds
    GROUP BY hub_id
),
reason_counts AS (
    SELECT hub_id, hold_reason, COUNT(*) AS hold_count
    FROM week2_holds
    GROUP BY hub_id, hold_reason
),
ranked_reasons AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY hub_id
            ORDER BY hold_count DESC, hold_reason
        ) AS reason_rank
    FROM reason_counts
),
top_two AS (
    SELECT
        hub_id,
        MAX(hold_reason) FILTER (WHERE reason_rank = 1) AS top_1_reason,
        MAX(hold_count) FILTER (WHERE reason_rank = 1) AS top_1_count,
        MAX(hold_reason) FILTER (WHERE reason_rank = 2) AS top_2_reason,
        MAX(hold_count) FILTER (WHERE reason_rank = 2) AS top_2_count
    FROM ranked_reasons
    WHERE reason_rank <= 2
    GROUP BY hub_id
)
SELECT
    h.hub_id,
    h.hub_name,
    t.total_holds,
    t.agent_side_holds,
    ROUND(t.agent_side_holds::numeric / NULLIF(t.total_holds, 0), 4) AS agent_side_share,
    r.top_1_reason,
    r.top_1_count,
    r.top_2_reason,
    r.top_2_count
FROM hub_totals t
JOIN hubs h ON h.hub_id = t.hub_id
JOIN top_two r ON r.hub_id = t.hub_id
ORDER BY h.hub_id;

-- ============================================================
-- Q4. What Happens to Held Orders
-- Count unique orders held at least once; classify by orders.final_status.
-- ============================================================

WITH held_order_ids AS (
    SELECT DISTINCT order_id
    FROM order_logs
    WHERE status = 'Hold'
),
held_orders AS (
    SELECT o.*
    FROM orders o
    JOIN held_order_ids h ON h.order_id = o.order_id
)
SELECT
    h.hub_id,
    h.hub_name,
    COUNT(*) AS held_orders,
    COUNT(*) FILTER (WHERE o.final_status = 'Delivered') AS finally_delivered,
    ROUND(
        COUNT(*) FILTER (WHERE o.final_status = 'Delivered')::numeric / COUNT(*), 4
    ) AS delivered_share,
    COUNT(*) FILTER (WHERE o.final_status = 'Returned') AS finally_returned,
    ROUND(
        COUNT(*) FILTER (WHERE o.final_status = 'Returned')::numeric / COUNT(*), 4
    ) AS returned_share,
    COUNT(*) FILTER (WHERE o.final_status = 'Hold') AS still_on_hold,
    ROUND(
        COUNT(*) FILTER (WHERE o.final_status = 'Hold')::numeric / COUNT(*), 4
    ) AS still_on_hold_share
FROM held_orders o
JOIN hubs h ON h.hub_id = o.hub_id
GROUP BY h.hub_id, h.hub_name
ORDER BY h.hub_id;

-- ============================================================
-- Q5. High-Return Agents
-- Return ratio = Returned outcome attempts / Assigned attempts.
-- Tenure must be strictly greater than 30 days on 26 October 2026.
-- ============================================================

WITH agent_counts AS (
    SELECT
        agent_id,
        COUNT(*) FILTER (WHERE status = 'Assigned') AS assigned_attempts,
        COUNT(*) FILTER (WHERE status = 'Returned') AS returned_attempts
    FROM order_logs
    WHERE event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY agent_id
)
SELECT
    a.agent_id,
    a.agent_name,
    a.hub_id,
    a.salary_type,
    DATE '2026-10-26' - a.joining_date AS tenure_days,
    c.assigned_attempts,
    c.returned_attempts,
    ROUND(c.returned_attempts::numeric / NULLIF(c.assigned_attempts, 0), 4) AS return_ratio
FROM agents a
JOIN agent_counts c ON c.agent_id = a.agent_id
WHERE DATE '2026-10-26' - a.joining_date > 30
  AND c.returned_attempts::numeric / NULLIF(c.assigned_attempts, 0) > 0.15
ORDER BY return_ratio DESC, c.returned_attempts DESC;

-- ============================================================
-- Q6. Cost per Delivered Order
-- Workday = agent-day with >=1 Assigned event. A Delivered outcome
-- is the delivered-order denominator in its event week.
-- Excludes COD and delivery_charge because they are not operating
-- costs in the company cost sheet.
-- ============================================================

WITH rule_values AS (
    SELECT
        MAX(value::numeric) FILTER (WHERE rule = 'Working days per month') AS working_days_per_month
    FROM rules
),
salary AS (
    SELECT
        MAX(monthly_salary) FILTER (WHERE salary_type = 'Fixed') AS fixed_monthly_salary,
        MAX(daily_allowance) FILTER (WHERE salary_type = 'Variable') AS variable_daily_allowance,
        MAX(allowance_per_delivery) FILTER (WHERE salary_type = 'Variable') AS variable_per_delivery
    FROM agent_salary
),
cost_values AS (
    SELECT
        MAX(amount_bdt) FILTER (WHERE what = 'A hold') AS hold_cost,
        MAX(amount_bdt) FILTER (WHERE what = 'A return') AS return_cost
    FROM costs
),
assigned_days AS (
    SELECT DISTINCT
        o.hub_id,
        l.agent_id,
        l.event_time::date AS work_date,
        CASE WHEN l.event_time::date <= DATE '2026-10-19' THEN 'Week 1' ELSE 'Week 2' END AS week_name,
        a.salary_type
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    JOIN agents a ON a.agent_id = l.agent_id
    WHERE l.status = 'Assigned'
      AND l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
),
payroll AS (
    SELECT
        d.hub_id,
        d.week_name,
        SUM(
            CASE WHEN d.salary_type = 'Fixed'
                 THEN s.fixed_monthly_salary / r.working_days_per_month ELSE 0 END
        ) AS fixed_pay,
        SUM(
            CASE WHEN d.salary_type = 'Variable'
                 THEN s.variable_daily_allowance ELSE 0 END
        ) AS variable_daily_pay
    FROM assigned_days d
    CROSS JOIN salary s
    CROSS JOIN rule_values r
    GROUP BY d.hub_id, d.week_name
),
variable_deliveries AS (
    SELECT
        o.hub_id,
        CASE WHEN l.event_time::date <= DATE '2026-10-19' THEN 'Week 1' ELSE 'Week 2' END AS week_name,
        COUNT(*) AS variable_delivered_events
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    JOIN agents a ON a.agent_id = l.agent_id
    WHERE l.status = 'Delivered'
      AND a.salary_type = 'Variable'
      AND l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id, week_name
),
operating_events AS (
    SELECT
        o.hub_id,
        CASE WHEN l.event_time::date <= DATE '2026-10-19' THEN 'Week 1' ELSE 'Week 2' END AS week_name,
        COUNT(*) FILTER (WHERE l.status = 'Delivered') AS delivered_orders,
        COUNT(*) FILTER (WHERE l.status = 'Hold') AS holds,
        COUNT(*) FILTER (WHERE l.status = 'Returned') AS returns
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id, week_name
)
SELECT
    h.hub_id,
    h.hub_name,
    e.week_name,
    COALESCE(p.fixed_pay, 0) AS fixed_pay,
    COALESCE(p.variable_daily_pay, 0) AS variable_daily_pay,
    COALESCE(v.variable_delivered_events, 0) * s.variable_per_delivery AS variable_delivery_allowance,
    e.holds * c.hold_cost AS hold_cost,
    e.returns * c.return_cost AS return_cost,
    COALESCE(p.fixed_pay, 0)
      + COALESCE(p.variable_daily_pay, 0)
      + COALESCE(v.variable_delivered_events, 0) * s.variable_per_delivery
      + e.holds * c.hold_cost
      + e.returns * c.return_cost AS total_operating_cost,
    e.delivered_orders,
    ROUND(
        (
          COALESCE(p.fixed_pay, 0)
          + COALESCE(p.variable_daily_pay, 0)
          + COALESCE(v.variable_delivered_events, 0) * s.variable_per_delivery
          + e.holds * c.hold_cost
          + e.returns * c.return_cost
        ) / NULLIF(e.delivered_orders, 0),
        2
    ) AS cost_per_delivered_order
FROM operating_events e
JOIN hubs h ON h.hub_id = e.hub_id
LEFT JOIN payroll p ON p.hub_id = e.hub_id AND p.week_name = e.week_name
LEFT JOIN variable_deliveries v ON v.hub_id = e.hub_id AND v.week_name = e.week_name
CROSS JOIN salary s
CROSS JOIN cost_values c
ORDER BY h.hub_id, e.week_name;

-- ============================================================
-- Q7. Agents Needed for the Forecast
-- Forecast expected orders are converted to attempts using each
-- hub's observed 14-day Assigned attempts / unique original orders.
-- Required agents = CEIL(forecast attempts / (7 * 40 * 85%)).
-- ============================================================

WITH historical_attempts AS (
    SELECT o.hub_id, COUNT(*) AS assigned_attempts
    FROM order_logs l
    JOIN orders o ON o.order_id = l.order_id
    WHERE l.status = 'Assigned'
      AND l.event_time::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY o.hub_id
),
historical_orders AS (
    SELECT hub_id, COUNT(*) AS total_orders
    FROM orders
    WHERE created_at::date BETWEEN DATE '2026-10-13' AND DATE '2026-10-26'
    GROUP BY hub_id
),
attempt_rate AS (
    SELECT
        a.hub_id,
        a.assigned_attempts::numeric / NULLIF(o.total_orders, 0) AS attempts_per_order
    FROM historical_attempts a
    JOIN historical_orders o ON o.hub_id = a.hub_id
),
active_agents AS (
    SELECT hub_id, COUNT(*) AS active_agents
    FROM agents
    WHERE active_status = 'Active'
    GROUP BY hub_id
),
standard AS (
    SELECT
        MAX(value::numeric) FILTER (WHERE rule = 'Standard attempts per agent per day') AS attempts_per_agent_day,
        MAX(value::numeric) FILTER (WHERE rule = 'Target utilisation') AS target_utilisation
    FROM rules
)
SELECT
    h.hub_id,
    h.hub_name,
    h.cluster,
    f.week_start,
    f.week_end,
    f.expected_orders,
    ROUND(r.attempts_per_order, 4) AS attempts_per_order,
    ROUND(f.expected_orders * r.attempts_per_order, 1) AS forecast_attempts,
    CEIL(
        (f.expected_orders * r.attempts_per_order)
        / (7 * s.attempts_per_agent_day * s.target_utilisation)
    )::integer AS required_agents,
    a.active_agents,
    CEIL(
        (f.expected_orders * r.attempts_per_order)
        / (7 * s.attempts_per_agent_day * s.target_utilisation)
    )::integer - a.active_agents AS staffing_gap
FROM volume_forecast f
JOIN hubs h ON h.hub_id = f.hub_id
JOIN attempt_rate r ON r.hub_id = f.hub_id
JOIN active_agents a ON a.hub_id = f.hub_id
CROSS JOIN standard s
ORDER BY f.week_start, h.hub_id;
