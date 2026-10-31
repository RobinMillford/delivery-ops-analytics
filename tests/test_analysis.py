
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.metrics import load_data, validate_data, calculate_analysis


def setup_results():
    data = load_data(ROOT / "data")
    return data, validate_data(data), calculate_analysis(data)


def test_all_eight_tables_validate_and_reconcile():
    data, validation, results = setup_results()
    assert validation["passed"] is True
    assert validation["relationships"]["one_outcome_per_assigned_attempt"] is True
    assert validation["relationships"]["final_status_matches_last_outcome"] is True
    assert results["strategic"]["orders_count"] == 22789
    assert results["strategic"]["assigned_attempts"] == 25595
    assert results["strategic"]["outcome_events"] == 25595


def test_utilisation_flags_expected_three_hubs():
    _, _, results = setup_results()
    flagged = set(results["q2"].loc[results["q2"]["week2_above_target"], "hub_id"])
    assert flagged == {"H01", "H03", "H04"}


def test_high_return_agents():
    _, _, results = setup_results()
    assert set(results["q5"]["agent_id"]) == {"A1045", "A1046", "A1047"}


def test_held_order_outcomes_reconcile():
    _, _, results = setup_results()
    q4 = results["q4"]
    assert int(q4["held_order_count"].sum()) == 2599
    assert int(q4["Delivered"].sum()) == 2118
    assert int(q4["Returned"].sum()) == 245
    assert int(q4["Hold"].sum()) == 236


def test_forecast_and_budget_scenario():
    _, _, results = setup_results()
    q7 = results["q7"]
    assert len(q7) == 24
    assert int(q7.loc[q7["hub_id"].eq("H04"), "required_agents"].max()) == 11
    strategic = results["strategic"]
    assert round(strategic["total_budget_spend"]) == 62800
    assert round(strategic["budget_remaining"]) == 7200
