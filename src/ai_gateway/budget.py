"""Durable admission accounting; unknown charges stay reserved until reconciled.

Amounts are integer micro-US dollars. Reservation ceilings must come from an
operator's provider contract, not a catalog estimate or request-supplied price.
SQLite serializes admission across connections/processes on one local database.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path


class BudgetDenied(RuntimeError):
    """A reservation cannot fit the account or request budget."""


def _amount(value: int) -> None:
    if type(value) is not int or not 0 <= value <= 2**53 - 1:
        raise ValueError("budget amounts must be nonnegative safe integers in micro-USD")


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError("account, request and attempt IDs must contain 1 to 128 characters")


class SQLiteBudgetLedger:
    def __init__(self, path: str | Path) -> None:
        if str(path) == ":memory:":
            raise ValueError("budget ledger requires a durable local file")
        self.path = str(Path(path).resolve())
        with self._transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS budget_accounts (
                account TEXT PRIMARY KEY, limit_microusd INTEGER NOT NULL,
                breached INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS budget_reservations (
                account TEXT NOT NULL REFERENCES budget_accounts(account),
                request_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
                ceiling_microusd INTEGER NOT NULL, actual_microusd INTEGER,
                PRIMARY KEY(account, attempt_id))""")
            db.execute("CREATE INDEX IF NOT EXISTS budget_request_idx "
                       "ON budget_reservations(account, request_id)")

    @contextmanager
    def _transaction(self):
        with closing(sqlite3.connect(self.path, timeout=5, isolation_level=None)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def configure_account(self, account: str, limit_microusd: int) -> None:
        _identifier(account)
        _amount(limit_microusd)
        with self._transaction() as db:
            used = self._exposure(db, account)
            if used > limit_microusd:
                raise BudgetDenied("new account limit is below outstanding exposure")
            db.execute("INSERT INTO budget_accounts(account, limit_microusd) VALUES (?, ?) "
                       "ON CONFLICT(account) DO UPDATE SET limit_microusd=excluded.limit_microusd",
                       (account, limit_microusd))

    @staticmethod
    def _exposure(db, account: str, request_id: str | None = None) -> int:
        sql = ("SELECT COALESCE(SUM(COALESCE(actual_microusd, ceiling_microusd)), 0) "
               "FROM budget_reservations WHERE account=?")
        args = [account]
        if request_id is not None:
            sql += " AND request_id=?"
            args.append(request_id)
        return db.execute(sql, args).fetchone()[0]

    def reserve(self, account: str, request_id: str, attempt_id: str, ceiling_microusd: int,
                *, request_limit_microusd: int | None = None) -> None:
        for value in (account, request_id, attempt_id):
            _identifier(value)
        _amount(ceiling_microusd)
        if request_limit_microusd is not None:
            _amount(request_limit_microusd)
        with self._transaction() as db:
            row = db.execute("SELECT * FROM budget_accounts WHERE account=?", (account,)).fetchone()
            if row is None:
                raise BudgetDenied("budget account is not configured")
            if row["breached"]:
                raise BudgetDenied("budget account is frozen after a charge-ceiling breach")
            if db.execute("SELECT 1 FROM budget_reservations WHERE account=? AND attempt_id=?",
                          (account, attempt_id)).fetchone():
                raise BudgetDenied("attempt ID has already been reserved; execution must not repeat")
            if self._exposure(db, account) + ceiling_microusd > row["limit_microusd"]:
                raise BudgetDenied("insufficient account budget")
            if request_limit_microusd is not None and (
                self._exposure(db, account, request_id) + ceiling_microusd > request_limit_microusd
            ):
                raise BudgetDenied("insufficient request budget")
            db.execute("INSERT INTO budget_reservations VALUES (?, ?, ?, ?, NULL)",
                       (account, request_id, attempt_id, ceiling_microusd))

    def settle(self, account: str, attempt_id: str, actual_microusd: int) -> bool:
        """Record confirmed charge, returning whether it exceeded the ceiling.

        Repeating the same settlement is safe; changing an already settled charge
        requires a separate audited correction process, not this method.
        """
        _amount(actual_microusd)
        with self._transaction() as db:
            row = db.execute("SELECT * FROM budget_reservations WHERE account=? AND attempt_id=?",
                             (account, attempt_id)).fetchone()
            if row is None:
                raise LookupError("unknown reservation for this account")
            if row["actual_microusd"] is not None and row["actual_microusd"] != actual_microusd:
                raise ValueError("reservation already has a different confirmed charge")
            db.execute("UPDATE budget_reservations SET actual_microusd=? "
                       "WHERE account=? AND attempt_id=?", (actual_microusd, account, attempt_id))
            breached = actual_microusd > row["ceiling_microusd"]
            if breached:
                db.execute("UPDATE budget_accounts SET breached=1 WHERE account=?", (account,))
            return breached

    def snapshot(self, account: str) -> dict[str, int | bool]:
        with self._transaction() as db:
            row = db.execute("SELECT * FROM budget_accounts WHERE account=?", (account,)).fetchone()
            if row is None:
                raise LookupError("unknown budget account")
            spent, reserved = db.execute("""SELECT
                COALESCE(SUM(actual_microusd), 0),
                COALESCE(SUM(CASE WHEN actual_microusd IS NULL THEN ceiling_microusd ELSE 0 END), 0)
                FROM budget_reservations WHERE account=?""", (account,)).fetchone()
            return {"limit_microusd": row["limit_microusd"], "spent_microusd": spent,
                    "reserved_microusd": reserved,
                    "available_microusd": row["limit_microusd"] - spent - reserved,
                    "breached": bool(row["breached"])}

    def pending(self, account: str) -> tuple[dict[str, object], ...]:
        with self._transaction() as db:
            rows = db.execute("SELECT request_id, attempt_id, ceiling_microusd "
                              "FROM budget_reservations WHERE account=? AND actual_microusd IS NULL "
                              "ORDER BY attempt_id", (account,)).fetchall()
            return tuple(dict(row) for row in rows)
