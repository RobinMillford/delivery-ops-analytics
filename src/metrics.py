
from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd

DATE_START = pd.Timestamp("2026-10-13")
WEEK1_END = pd.Timestamp("2026-10-19")
DATE_END = pd.Timestamp("2026-10-26")
FORECAST_DAYS_PER_WEEK = 7
STANDARD_ATTEMPTS = 40
TARGET_UTILISATION = 0.85
AGENT_SIDE_REASONS = {"Late Dispatch", "Not Attempted", "Agent Time Shortage"}

def load_data(data_dir: str | Path = "data") -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    required = {
        "hubs": "hubs.csv",
        "agents": "agents.csv",
        "orders": "orders.csv",
        "order_logs": "order_logs.csv",
        "agent_salary": "agent_salary.csv",
        "costs": "costs.csv",
        "rules": "rules.csv",
        "volume_forecast": "volume_forecast.csv",
    }
    missing = [fname for fname in required.values() if not (data_dir / fname).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required data files in {data_dir}: {', '.join(missing)}")

    data = {key: pd.read_csv(data_dir / fname) for key, fname in required.items()}
    data["agents"]["joining_date"] = pd.to_datetime(data["agents"]["joining_date"], errors="raise")
    data["orders"]["created_at"] = pd.to_datetime(data["orders"]["created_at"], errors="raise")
    data["order_logs"]["event_time"] = pd.to_datetime(data["order_logs"]["event_time"], errors="raise")
    data["volume_forecast"]["week_start"] = pd.to_datetime(data["volume_forecast"]["week_start"], errors="raise")
    data["volume_forecast"]["week_end"] = pd.to_datetime(data["volume_forecast"]["week_end"], errors="raise")
    return data

def validate_data(data: dict[str, pd.DataFrame]) -> dict:
    expected = {
        "hubs": {"hub_id", "hub_name", "cluster"},
        "agents": {"agent_id", "agent_name", "hub_id", "salary_type", "joining_date", "active_status"},
        "orders": {"order_id", "hub_id", "created_at", "final_status", "cod_amount", "delivery_charge"},
        "order_logs": {"log_id", "order_id", "agent_id", "status", "hold_reason", "event_time", "attempt_no"},
        "agent_salary": {"salary_type", "monthly_salary", "daily_allowance", "allowance_per_delivery"},
        "costs": {"what", "amount_bdt", "when_charged"},
        "rules": {"rule", "value"},
        "volume_forecast": {"hub_id", "week_start", "week_end", "expected_orders"},
    }
    checks = []
    for table, cols in expected.items():
        missing_cols = sorted(cols - set(data[table].columns))
        checks.append({
            "table": table,
            "rows": len(data[table]),
            "missing_columns": missing_cols,
            "duplicate_rows": int(data[table].duplicated().sum()),
            "null_cells": int(data[table].isna().sum().sum()),
        })
    # Key uniqueness and relationships
    orders = data["orders"]
    logs = data["order_logs"]
    agents = data["agents"]
    relation_checks = {
        "orders_unique": bool(orders["order_id"].is_unique),
        "logs_unique": bool(logs["log_id"].is_unique),
        "agents_unique": bool(agents["agent_id"].is_unique),
        "logs_all_orders_match": bool(logs["order_id"].isin(orders["order_id"]).all()),
        "logs_all_agents_match": bool(logs["agent_id"].isin(agents["agent_id"]).all()),
        "orders_all_hubs_match": bool(orders["hub_id"].isin(data["hubs"]["hub_id"]).all()),
        "forecast_all_hubs_match": bool(data["volume_forecast"]["hub_id"].isin(data["hubs"]["hub_id"]).all()),
        "hold_reason_present_on_hold_events": bool(
            logs.loc[logs["status"].eq("Hold"), "hold_reason"].notna().all()
        ),
    }
    attempt_counts = logs.pivot_table(
        index=["order_id", "attempt_no"], columns="status", values="log_id",
        aggfunc="count", fill_value=0
    )
    assigned = attempt_counts.get("Assigned", pd.Series(0, index=attempt_counts.index))
    outcome_total = sum(
        attempt_counts.get(status, pd.Series(0, index=attempt_counts.index))
        for status in ["Delivered", "Hold", "Returned"]
    )
    relation_checks["one_outcome_per_assigned_attempt"] = bool(assigned.eq(outcome_total).all())
    # Every order's final_status should agree with its last logged outcome.
    order_events = logs[logs["status"].isin(["Delivered", "Hold", "Returned"])].copy()
    order_events = order_events.sort_values(["order_id", "attempt_no", "event_time"])
    last_status = order_events.groupby("order_id").tail(1).set_index("order_id")["status"]
    final_map = orders.set_index("order_id")["final_status"]
    relation_checks["final_status_matches_last_outcome"] = bool(
        final_map.reindex(last_status.index).eq(last_status).all()
    )
    inactive_ids = set(agents.loc[agents["active_status"].eq("Inactive"), "agent_id"])
    inactive_week2_attempts = logs[
        logs["agent_id"].isin(inactive_ids)
        & logs["status"].eq("Assigned")
        & pd.to_datetime(logs["event_time"]).dt.date.astype(str).ge("2026-10-20")
    ]
    relation_checks["inactive_agents_have_no_week2_attempts"] = inactive_week2_attempts.empty
    errors = [c for c in checks if c["missing_columns"] or c["duplicate_rows"]]
    return {
        "tables": checks,
        "relationships": relation_checks,
        "notes": ["order_logs.hold_reason is intentionally null for non-Hold status events."],
        "passed": not errors and all(relation_checks.values()),
    }

def _rule_value(rules: pd.DataFrame, key_fragment: str, cast=float):
    rows = rules[rules["rule"].str.contains(key_fragment, case=False, regex=False)]
    if rows.empty:
        raise KeyError(f"Required company rule not found: {key_fragment}")
    value = rows.iloc[0]["value"]
    if cast is int:
        return int(float(value))
    if cast is float:
        return float(value)
    return value

def calculate_analysis(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame | dict]:
    hubs = data["hubs"].copy()
    agents = data["agents"].copy()
    orders = data["orders"].copy()
    logs = data["order_logs"].copy()
    salaries = data["agent_salary"].copy()
    costs = data["costs"].copy()
    rules = data["rules"].copy()
    forecast = data["volume_forecast"].copy()

    standard = _rule_value(rules, "Standard attempts per agent per day", float)
    target = _rule_value(rules, "Target utilisation", float)
    workdays_month = _rule_value(rules, "Working days per month", int)
    new_agent_speed = _rule_value(rules, "New agent speed", float)
    hold_reduction = _rule_value(rules, "Hold programme removes agent-side holds", float)
    programme_days = _rule_value(rules, "Days for the hold programme", int)

    cost_lookup = dict(zip(costs["what"], costs["amount_bdt"]))
    hold_cost = float(cost_lookup["A hold"])
    return_cost = float(cost_lookup["A return"])
    hire_cost = float(cost_lookup["Hiring a new agent"])
    transfer_cost = float(cost_lookup["Moving an agent to another hub"])
    hold_programme_cost = float(cost_lookup["Hold reduction programme"])

    # Link every event to the operational hub via its order. All event dates are local data dates.
    events = logs.merge(
        orders[["order_id", "hub_id", "created_at", "final_status"]],
        on="order_id", how="left", validate="many_to_one"
    )
    events["event_date"] = events["event_time"].dt.normalize()
    events["week"] = np.where(
        events["event_date"].between(DATE_START, WEEK1_END), "Week 1", "Week 2"
    )
    events["week_num"] = np.where(events["week"].eq("Week 1"), 1, 2)

    # Q1: roster x date grid. Inactive staff are available only through the end of Week 1.
    dates = pd.DataFrame({"event_date": pd.date_range(DATE_START, DATE_END, freq="D")})
    roster = agents.merge(dates, how="cross")
    roster = roster[
        roster["active_status"].eq("Active")
        | (roster["active_status"].eq("Inactive") & roster["event_date"].le(WEEK1_END))
    ].copy()
    per_agent_day = (
        events.pivot_table(
            index=["event_date", "agent_id", "hub_id"],
            columns="status", values="log_id", aggfunc="count", fill_value=0
        )
        .reset_index()
    )
    for status in ["Assigned", "Delivered", "Hold", "Returned"]:
        if status not in per_agent_day.columns:
            per_agent_day[status] = 0
    per_agent_day = per_agent_day.rename(columns={
        "Assigned": "assigned_attempts",
        "Delivered": "delivered_attempts",
        "Hold": "hold_attempts",
        "Returned": "returned_attempts",
    })
    q1_daily = roster.merge(
        per_agent_day[["event_date", "agent_id", "hub_id", "assigned_attempts",
                       "delivered_attempts", "hold_attempts", "returned_attempts"]],
        on=["event_date", "agent_id", "hub_id"], how="left", validate="one_to_one"
    )
    for col in ["assigned_attempts", "delivered_attempts", "hold_attempts", "returned_attempts"]:
        q1_daily[col] = q1_daily[col].fillna(0).astype(int)
    q1_daily = q1_daily.sort_values(["event_date", "hub_id", "agent_id"]).reset_index(drop=True)
    q1_daily["event_date"] = q1_daily["event_date"].dt.date

    q1_hub = q1_daily.groupby("hub_id", as_index=False).agg(
        delivered_attempts=("delivered_attempts", "sum"),
        available_agent_days=("agent_id", "size"),
    ).merge(hubs, on="hub_id", how="left")
    q1_hub["avg_deliveries_per_agent_day"] = (
        q1_hub["delivered_attempts"] / q1_hub["available_agent_days"]
    )
    q1_hub = q1_hub[["hub_id", "hub_name", "cluster", "delivered_attempts",
                     "available_agent_days", "avg_deliveries_per_agent_day"]]

    # Q2: use all agents in Week 1; only Active agents in Week 2, per the company note.
    headcounts = agents.groupby("hub_id").agg(
        week1_agents=("agent_id", "size"),
        week2_agents=("active_status", lambda s: int(s.eq("Active").sum())),
    ).reset_index()
    attempts_by_week = (
        events[events["status"].eq("Assigned")]
        .groupby(["hub_id", "week"]).size().unstack(fill_value=0).reset_index()
    )
    for w in ["Week 1", "Week 2"]:
        if w not in attempts_by_week.columns:
            attempts_by_week[w] = 0
    q2 = attempts_by_week.merge(headcounts, on="hub_id").merge(hubs, on="hub_id")
    q2["week1_utilisation"] = q2["Week 1"] / (q2["week1_agents"] * standard * 7)
    q2["week2_utilisation"] = q2["Week 2"] / (q2["week2_agents"] * standard * 7)
    q2["week1_above_target"] = q2["week1_utilisation"] > target
    q2["week2_above_target"] = q2["week2_utilisation"] > target
    q2["attempt_change_pct"] = (q2["Week 2"] / q2["Week 1"] - 1) * 100
    q2 = q2[["hub_id", "hub_name", "cluster", "Week 1", "Week 2", "week1_agents",
             "week2_agents", "week1_utilisation", "week2_utilisation",
             "week2_above_target", "attempt_change_pct"]].sort_values("hub_id")

    # Q3: Week 2 holds, agent-side share, and top two reasons.
    w2_holds = events[(events["status"].eq("Hold")) & (events["week"].eq("Week 2"))].copy()
    w2_holds["hold_side"] = np.where(w2_holds["hold_reason"].isin(AGENT_SIDE_REASONS),
                                      "Agent-side", "Customer-side")
    q3_base = w2_holds.groupby("hub_id").agg(
        total_holds=("log_id", "count"),
        agent_side_holds=("hold_side", lambda x: int(x.eq("Agent-side").sum())),
    ).reset_index()
    q3_base["agent_side_share"] = q3_base["agent_side_holds"] / q3_base["total_holds"]
    reasons = (w2_holds.groupby(["hub_id", "hold_reason"]).size()
               .reset_index(name="hold_count")
               .sort_values(["hub_id", "hold_count", "hold_reason"],
                            ascending=[True, False, True]))
    reasons["reason_rank"] = reasons.groupby("hub_id").cumcount() + 1
    top_reasons = reasons[reasons["reason_rank"].le(2)].pivot(
        index="hub_id", columns="reason_rank", values=["hold_reason", "hold_count"]
    )
    top_reasons.columns = [f"top_{rank}_{field}" for field, rank in top_reasons.columns]
    q3 = q3_base.merge(top_reasons.reset_index(), on="hub_id").merge(hubs, on="hub_id")
    q3 = q3[["hub_id", "hub_name", "total_holds", "agent_side_holds", "agent_side_share",
             "top_1_hold_reason", "top_1_hold_count", "top_2_hold_reason", "top_2_hold_count"]]

    # Q4: unique orders with at least one hold, classified by final order status.
    held_ids = events.loc[events["status"].eq("Hold"), "order_id"].drop_duplicates()
    held_orders = orders[orders["order_id"].isin(held_ids)].copy()
    q4 = held_orders.groupby(["hub_id", "final_status"]).size().unstack(fill_value=0).reset_index()
    for status in ["Delivered", "Returned", "Hold"]:
        if status not in q4.columns:
            q4[status] = 0
    q4["held_order_count"] = q4[["Delivered", "Returned", "Hold"]].sum(axis=1)
    for status in ["Delivered", "Returned", "Hold"]:
        q4[f"{status.lower()}_share"] = q4[status] / q4["held_order_count"]
    q4 = q4.merge(hubs, on="hub_id")
    q4 = q4[["hub_id", "hub_name", "held_order_count", "Delivered", "delivered_share",
             "Returned", "returned_share", "Hold", "hold_share"]].sort_values("hub_id")

    # Q5: return ratio is Returned outcomes / Assigned attempts per agent.
    agent_perf = events.pivot_table(
        index="agent_id", columns="status", values="log_id", aggfunc="count", fill_value=0
    ).reset_index()
    for status in ["Assigned", "Delivered", "Hold", "Returned"]:
        if status not in agent_perf.columns:
            agent_perf[status] = 0
    agent_perf = agent_perf.merge(agents, on="agent_id", how="left")
    agent_perf["tenure_days"] = (DATE_END - agent_perf["joining_date"]).dt.days
    agent_perf["return_ratio"] = np.where(
        agent_perf["Assigned"].gt(0), agent_perf["Returned"] / agent_perf["Assigned"], 0
    )
    q5 = agent_perf[
        agent_perf["tenure_days"].gt(30) & agent_perf["return_ratio"].gt(0.15)
    ].copy().sort_values(["return_ratio", "Returned"], ascending=[False, False])
    q5 = q5[["agent_id", "agent_name", "hub_id", "salary_type", "tenure_days",
             "Assigned", "Returned", "return_ratio"]]

    # Q6: operating cost is accrued in the week of the event.
    # Workday = an agent-day with >=1 Assigned event. Per-delivery allowance applies to
    # successful Delivered outcomes for Variable agents.
    assigned_events = events[events["status"].eq("Assigned")].copy()
    assigned_events = assigned_events.merge(
        agents[["agent_id", "salary_type"]], on="agent_id", how="left", validate="many_to_one"
    )
    working_days = assigned_events.groupby(["hub_id", "agent_id", "salary_type", "event_date", "week"]).size().reset_index(name="attempts")
    salary_map = salaries.set_index("salary_type")
    working_days["fixed_pay"] = np.where(
        working_days["salary_type"].eq("Fixed"),
        float(salary_map.loc["Fixed", "monthly_salary"]) / workdays_month, 0
    )
    working_days["variable_daily"] = np.where(
        working_days["salary_type"].eq("Variable"),
        float(salary_map.loc["Variable", "daily_allowance"]), 0
    )
    delivered_by_agent_day = (
        events[events["status"].eq("Delivered")]
        .merge(agents[["agent_id", "salary_type"]], on="agent_id", validate="many_to_one")
        .query("salary_type == 'Variable'")
        .groupby(["hub_id", "agent_id", "event_date", "week"]).size()
        .rename("variable_deliveries").reset_index()
    )
    working_days = working_days.merge(
        delivered_by_agent_day, on=["hub_id", "agent_id", "event_date", "week"], how="left"
    )
    working_days["variable_deliveries"] = working_days["variable_deliveries"].fillna(0)
    working_days["variable_delivery_allowance"] = (
        working_days["variable_deliveries"] * float(salary_map.loc["Variable", "allowance_per_delivery"])
    )
    pay_by_week = working_days.groupby(["hub_id", "week"]).agg(
        fixed_pay=("fixed_pay", "sum"),
        variable_daily=("variable_daily", "sum"),
        variable_delivery_allowance=("variable_delivery_allowance", "sum"),
        agent_workdays=("agent_id", "size"),
    ).reset_index()
    event_costs = events.groupby(["hub_id", "week", "status"]).size().unstack(fill_value=0).reset_index()
    for status in ["Delivered", "Hold", "Returned"]:
        if status not in event_costs.columns:
            event_costs[status] = 0
    q6 = pay_by_week.merge(event_costs, on=["hub_id", "week"], how="left").merge(hubs, on="hub_id")
    q6["hold_cost"] = q6["Hold"] * hold_cost
    q6["return_cost"] = q6["Returned"] * return_cost
    q6["total_operating_cost"] = (
        q6["fixed_pay"] + q6["variable_daily"] + q6["variable_delivery_allowance"]
        + q6["hold_cost"] + q6["return_cost"]
    )
    q6["delivered_orders"] = q6["Delivered"]
    q6["cost_per_delivered_order"] = q6["total_operating_cost"] / q6["delivered_orders"]
    q6 = q6[["hub_id", "hub_name", "week", "agent_workdays", "fixed_pay", "variable_daily",
             "variable_delivery_allowance", "hold_cost", "return_cost", "total_operating_cost",
             "delivered_orders", "cost_per_delivered_order"]].sort_values(["hub_id", "week"])

    # Q7: 14-day average attempts per order is the base forecast conversion.
    hist_attempts = events[events["status"].eq("Assigned")].groupby("hub_id").size().rename("historical_attempts")
    hist_orders = orders.groupby("hub_id").size().rename("historical_orders")
    attempt_rates = pd.concat([hist_attempts, hist_orders], axis=1).reset_index()
    attempt_rates["attempts_per_order"] = attempt_rates["historical_attempts"] / attempt_rates["historical_orders"]
    active_counts = agents[agents["active_status"].eq("Active")].groupby("hub_id").size().rename("active_agents")
    q7 = (forecast.merge(attempt_rates[["hub_id", "attempts_per_order"]], on="hub_id")
          .merge(active_counts, on="hub_id").merge(hubs, on="hub_id"))
    q7["forecast_attempts"] = q7["expected_orders"] * q7["attempts_per_order"]
    q7["required_agents"] = np.ceil(q7["forecast_attempts"] / (7 * standard * target)).astype(int)
    q7["staffing_gap"] = q7["required_agents"] - q7["active_agents"]
    q7["week_label"] = q7.apply(lambda r: f"{r['week_start']:%d %b} - {r['week_end']:%d %b}", axis=1)
    q7 = q7[["hub_id", "hub_name", "cluster", "week_start", "week_end", "week_label",
             "expected_orders", "attempts_per_order", "forecast_attempts", "required_agents",
             "active_agents", "staffing_gap"]].sort_values(["week_start", "hub_id"])

    # Sensitivity: latest-week attempt rate, used for H03 hold-programme and operational stress test.
    week2_orders = (orders[orders["created_at"].between(DATE_START + pd.Timedelta(days=7), DATE_END + pd.Timedelta(days=1)-pd.Timedelta(seconds=1))]
                    .groupby("hub_id").size().rename("week2_orders"))
    week2_attempts = (events[(events["status"].eq("Assigned")) & (events["week"].eq("Week 2"))]
                      .groupby("hub_id").size().rename("week2_attempts"))
    recent_rates = pd.concat([week2_attempts, week2_orders], axis=1).reset_index()
    recent_rates["week2_attempts_per_order"] = recent_rates["week2_attempts"] / recent_rates["week2_orders"]

    # Scenario: transfer two qualified Fixed agents from H02 -> H01; programme in H03;
    # two Fixed hires at H04. H03 programme is modeled as a linear ramp to 50% reduction over 14 days.
    h3_w2_hold = w2_holds[(w2_holds["hub_id"].eq("H03")) & (w2_holds["hold_side"].eq("Agent-side"))].shape[0]
    h3_w2_orders = int(week2_orders.loc["H03"])
    h3_agent_holds_per_order = h3_w2_hold / h3_w2_orders
    h3_recent_rate = float(recent_rates.loc[recent_rates["hub_id"].eq("H03"), "week2_attempts_per_order"].iloc[0])
    programme_progress = [0.25, 0.75, 1.0, 1.0]  # average fraction of full effect in weeks 1-4
    programme_weekly = forecast[forecast["hub_id"].eq("H03")].sort_values("week_start").copy()
    programme_weekly["programme_progress"] = programme_progress
    programme_weekly["hold_reduction_fraction"] = hold_reduction * programme_weekly["programme_progress"]
    programme_weekly["agent_side_hold_rate_per_order"] = h3_agent_holds_per_order
    programme_weekly["avoided_holds"] = (
        programme_weekly["expected_orders"] * h3_agent_holds_per_order
        * programme_weekly["hold_reduction_fraction"]
    )
    programme_weekly["adjusted_attempts_per_order"] = (
        h3_recent_rate - h3_agent_holds_per_order * programme_weekly["hold_reduction_fraction"]
    )
    programme_weekly["adjusted_attempts"] = (
        programme_weekly["expected_orders"] * programme_weekly["adjusted_attempts_per_order"]
    )
    programme_weekly["utilisation_vs_standard"] = programme_weekly["adjusted_attempts"] / (12 * standard * 7)
    programme_weekly["required_agents_at_target"] = np.ceil(
        programme_weekly["adjusted_attempts"] / (7 * standard * target)
    ).astype(int)
    programme_weekly["hold_cost_saving_bdt"] = programme_weekly["avoided_holds"] * hold_cost

    # New Fixed hire at H04: estimated first-month salary plus hiring costs.
    new_agent_month_attempts = (7 * standard * new_agent_speed) + ((workdays_month - 7) * standard * target)
    h04_deliver_rate = float(
        events[(events["hub_id"].eq("H04")) & (events["status"].eq("Delivered"))].shape[0]
        / events[(events["hub_id"].eq("H04")) & (events["status"].eq("Assigned"))].shape[0]
    )
    estimated_h04_deliveries_per_new_agent = new_agent_month_attempts * h04_deliver_rate
    fixed_monthly_salary = float(salary_map.loc["Fixed", "monthly_salary"])
    variable_monthly_cost = (
        float(salary_map.loc["Variable", "daily_allowance"]) * workdays_month
        + float(salary_map.loc["Variable", "allowance_per_delivery"]) * estimated_h04_deliveries_per_new_agent
    )
    recommended_new_hires = 2
    recommended_transfers = 2
    total_hire_salary = recommended_new_hires * fixed_monthly_salary
    total_hiring_fees = recommended_new_hires * hire_cost
    total_transfer_cost = recommended_transfers * transfer_cost
    total_programme_cost = hold_programme_cost
    total_budget = total_hire_salary + total_hiring_fees + total_transfer_cost + total_programme_cost
    programme_holds_avoided = float(programme_weekly["avoided_holds"].sum())
    programme_cash_saving = programme_holds_avoided * hold_cost
    programme_net_cash_benefit = programme_cash_saving - hold_programme_cost

    strategic = {
        "standard_attempts_per_agent_per_day": standard,
        "target_utilisation": target,
        "workdays_per_month": workdays_month,
        "new_agent_speed_first_7_days": new_agent_speed,
        "agent_side_hold_reduction_full_effect": hold_reduction,
        "hold_programme_days_to_full_effect": programme_days,
        "week2_utilisation_by_hub": q2.set_index("hub_id")["week2_utilisation"].to_dict(),
        "eligible_transfer_sources": ["H02", "H05"],
        "transfer_recommendation": [
            {"agent_id": "A1018", "agent_name": "Lorus Brannick", "from_hub": "H02", "to_hub": "H01",
             "salary_type": "Fixed", "delivery_ratio": 270/291, "return_ratio": 9/291},
            {"agent_id": "A1015", "agent_name": "Toren Larkin", "from_hub": "H02", "to_hub": "H01",
             "salary_type": "Fixed", "delivery_ratio": 308/339, "return_ratio": 9/339},
        ],
        "new_hires": [
            {"hub_id": "H04", "hub_name": "Hillcrest", "count": 2, "salary_type": "Fixed",
             "monthly_salary_per_agent": fixed_monthly_salary, "hire_fee_per_agent": hire_cost}
        ],
        "programme_hub": "H03",
        "programme_cost": hold_programme_cost,
        "programme_weekly": programme_weekly,
        "programme_holds_avoided": programme_holds_avoided,
        "programme_cash_saving": programme_cash_saving,
        "programme_net_cash_benefit": programme_net_cash_benefit,
        "new_agent_month_attempts": new_agent_month_attempts,
        "h04_delivery_rate": h04_deliver_rate,
        "estimated_h04_deliveries_per_new_agent": estimated_h04_deliveries_per_new_agent,
        "fixed_monthly_salary_per_new_agent": fixed_monthly_salary,
        "variable_monthly_cost_per_new_agent_at_h04": variable_monthly_cost,
        "total_hire_salary": total_hire_salary,
        "total_hiring_fees": total_hiring_fees,
        "total_transfer_cost": total_transfer_cost,
        "total_programme_cost": total_programme_cost,
        "total_budget_spend": total_budget,
        "budget_limit": 70000,
        "budget_remaining": 70000-total_budget,
        "strict_85pct_alternative": {
            "description": "Hire 1 additional Variable agent at H03 rather than fund the hold programme; retain 2 Fixed hires at H04 and 2 transfers H02->H01.",
            "h03_variable_salary_month": (
                float(salary_map.loc["Variable", "daily_allowance"]) * workdays_month
                + float(salary_map.loc["Variable", "allowance_per_delivery"])
                * new_agent_month_attempts
                * float(events[(events["hub_id"].eq("H03")) & (events["status"].eq("Delivered"))].shape[0]
                        / events[(events["hub_id"].eq("H03")) & (events["status"].eq("Assigned"))].shape[0])
            ),
            "total_cost": None,
        }
    }
    h3_variable_salary = strategic["strict_85pct_alternative"]["h03_variable_salary_month"]
    strategic["strict_85pct_alternative"]["total_cost"] = (
        total_hire_salary + total_hiring_fees + total_transfer_cost
        + (h3_variable_salary + hire_cost)
    )

    # All-source check: the latest logged outcome should equal the final_status in orders.
    last_outcomes = (events[events["status"].isin(["Delivered", "Hold", "Returned"])]
                     .sort_values(["order_id", "attempt_no", "event_time"])
                     .groupby("order_id").tail(1)[["order_id", "status"]]
                     .rename(columns={"status": "last_log_status"}))
    status_map = {"Delivered": "Delivered", "Hold": "Hold", "Returned": "Returned"}
    reconciled = orders[["order_id", "final_status"]].merge(last_outcomes, on="order_id", how="left")
    reconciled["mapped_last_status"] = reconciled["last_log_status"].map(status_map)
    strategic["final_status_reconciliation_passed"] = bool(
        reconciled["final_status"].eq(reconciled["mapped_last_status"]).all()
    )
    strategic["assigned_attempts"] = int(events["status"].eq("Assigned").sum())
    strategic["outcome_events"] = int(events["status"].isin(["Delivered", "Hold", "Returned"]).sum())
    strategic["orders_count"] = int(orders["order_id"].nunique())
    strategic["agent_side_reasons"] = sorted(AGENT_SIDE_REASONS)

    return {
        "events": events,
        "q1_daily": q1_daily,
        "q1_hub": q1_hub,
        "q2": q2,
        "q3": q3,
        "q3_reasons": reasons,
        "q4": q4,
        "q5": q5,
        "q6": q6,
        "q7": q7,
        "recent_rates": recent_rates,
        "programme_weekly": programme_weekly,
        "strategic": strategic,
    }
