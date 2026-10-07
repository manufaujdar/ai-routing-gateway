from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context

import pytest

from ai_gateway.budget import BudgetDenied, SQLiteBudgetLedger


def test_concurrent_reservations_cannot_oversubscribe_and_survive_restart(tmp_path):
    path = tmp_path / "budget.sqlite"
    ledger = SQLiteBudgetLedger(path)
    ledger.configure_account("tenant-a", 100)

    def reserve(index):
        try:
            SQLiteBudgetLedger(path).reserve("tenant-a", f"request-{index}", str(index), 30)
            return True
        except BudgetDenied:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(8))) == 3
    assert SQLiteBudgetLedger(path).snapshot("tenant-a")["reserved_microusd"] == 90


def test_reconciliation_is_account_scoped_and_idempotent(tmp_path):
    ledger = SQLiteBudgetLedger(tmp_path / "budget.sqlite")
    ledger.configure_account("a", 100)
    ledger.configure_account("b", 100)
    ledger.reserve("a", "r", "attempt", 60)
    with pytest.raises(LookupError):
        ledger.settle("b", "attempt", 10)
    ledger.settle("a", "attempt", 10)
    ledger.settle("a", "attempt", 10)
    assert ledger.snapshot("a")["available_microusd"] == 90
    with pytest.raises(ValueError):
        ledger.settle("a", "attempt", 11)
    with pytest.raises(BudgetDenied):
        ledger.reserve("a", "r", "attempt", 60)


def test_request_budget_includes_prior_spend_and_pending_calls(tmp_path):
    ledger = SQLiteBudgetLedger(tmp_path / "budget.sqlite")
    ledger.configure_account("a", 1000)
    ledger.reserve("a", "r", "one", 40, request_limit_microusd=50)
    ledger.settle("a", "one", 20)
    with pytest.raises(BudgetDenied):
        ledger.reserve("a", "r", "two", 31, request_limit_microusd=50)
    ledger.reserve("a", "r", "two", 30, request_limit_microusd=50)


def test_overcharge_is_recorded_and_freezes_new_admission(tmp_path):
    ledger = SQLiteBudgetLedger(tmp_path / "budget.sqlite")
    ledger.configure_account("a", 100)
    ledger.reserve("a", "r", "one", 30)
    assert ledger.settle("a", "one", 120) is True
    snapshot = ledger.snapshot("a")
    assert snapshot["spent_microusd"] == 120
    assert snapshot["breached"] is True
    with pytest.raises(BudgetDenied):
        ledger.reserve("a", "r2", "two", 1)


@pytest.mark.parametrize("amount", [-1, True, 1.5, float("inf")])
def test_budget_amounts_are_exact_nonnegative_integers(tmp_path, amount):
    with pytest.raises(ValueError):
        SQLiteBudgetLedger(tmp_path / "budget.sqlite").configure_account("a", amount)


def _reserve_in_process(arguments):
    path, index = arguments
    try:
        SQLiteBudgetLedger(path).reserve("a", str(index), str(index), 10)
        return True
    except BudgetDenied:
        return False


def test_separate_processes_share_atomic_budget(tmp_path):
    path = str(tmp_path / "shared.sqlite")
    ledger = SQLiteBudgetLedger(path)
    ledger.configure_account("a", 100)
    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("spawn")) as pool:
        admitted = sum(pool.map(_reserve_in_process, [(path, i) for i in range(40)]))
    assert admitted == 10
    assert ledger.snapshot("a")["reserved_microusd"] == 100
