from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "quant"))
from contract_check import (  # noqa: E402
    ContractError,
    Schema,
    align,
    canonical,
    golden_result,
    load_json,
    parse_json,
    recover,
    transaction,
    validate_trace,
)

BUNDLE = ROOT / "contracts" / "quant" / "v1"


class MessageContracts(unittest.TestCase):
    def test_shared_messages(self):
        schema = Schema(load_json(BUNDLE / "schema.json"))
        cases = load_json(BUNDLE / "messages.json")["cases"]
        self.assertEqual(len({case["name"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["name"]):
                if case["valid"]:
                    schema.check(
                        case["definition"],
                        parse_json(case["raw"]) if "raw" in case else case["value"],
                    )
                else:
                    with self.assertRaises(ContractError):
                        schema.check(
                            case["definition"],
                            parse_json(case["raw"]) if "raw" in case else case["value"],
                        )

    def test_unknown_schema_keyword_fails_closed(self):
        schema = Schema({"$defs": {"bad": {"type": "string", "notImplemented": True}}})
        with self.assertRaises(ContractError):
            schema.check("bad", "value")

    def test_duplicate_json_fields_rejected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"quantity":"1","quantity":"100"}')
            with self.assertRaises(ContractError):
                load_json(path)

    def test_state_and_permission_policy(self):
        policy = load_json(BUNDLE / "policy.json")
        for state in ("COMPLETED", "FAILED", "STOPPED"):
            self.assertEqual(policy["states"][state], [])
        self.assertEqual(
            [phase for phase, rule in policy["phases"].items() if rule["trade"]], ["bar"]
        )
        self.assertLess(
            policy["limits"]["queue_bytes"],
            policy["limits"]["queue_items"] * policy["limits"]["message_bytes"],
        )

    def test_all_registered_methods_have_request_and_response_schemas(self):
        registry = load_json(BUNDLE / "methods.json")
        schema = load_json(BUNDLE / "schema.json")["$defs"]
        self.assertEqual(set(registry["requests"]), set(registry["responses"]))
        for definition in (
            list(registry["requests"].values())
            + list(registry["responses"].values())
            + list(registry["notifications"].values())
        ):
            self.assertIn(definition, schema)
        messages = load_json(BUNDLE / "messages.json")["cases"]
        for definition in schema:
            for valid in (True, False):
                self.assertTrue(
                    any(
                        case["definition"] == definition and case["valid"] == valid
                        for case in messages
                    ),
                    (definition, valid),
                )
        for definition, rule in schema.items():
            for field in rule.get("required", []):
                self.assertTrue(
                    any(
                        case["definition"] == definition
                        and not case["valid"]
                        and "value" in case
                        and isinstance(case["value"], dict)
                        and field not in case["value"]
                        for case in messages
                    ),
                    (definition, field),
                )

    def test_callback_barrier_sequences(self):
        policy = load_json(BUNDLE / "policy.json")
        for case in load_json(BUNDLE / "traces.json")["cases"]:
            with self.subTest(case=case["name"]):
                if case["valid"]:
                    validate_trace(case["events"], policy)
                else:
                    with self.assertRaises(ContractError):
                        validate_trace(case["events"], policy)


class AccountingGoldens(unittest.TestCase):
    def test_step_rounding_is_exact_at_34_digit_boundary(self):
        from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, localcontext

        with localcontext() as context:
            context.prec = 34
            self.assertEqual(
                align(
                    Decimal("0.1499999999999999999999999999999999"), Decimal("0.1"), ROUND_HALF_UP
                ),
                Decimal("0.1"),
            )
            self.assertEqual(
                align(Decimal("0.2999999999999999999999999999999999"), Decimal("0.1"), ROUND_FLOOR),
                Decimal("0.2"),
            )
            self.assertEqual(
                align(
                    Decimal("0.3000000000000000000000000000000001"), Decimal("0.1"), ROUND_CEILING
                ),
                Decimal("0.4"),
            )

    def test_fixed_accounting_expected_values(self):
        cases = load_json(BUNDLE / "goldens.json")["cases"]
        required = {
            "two_buys_compete",
            "favorable_fill_releases",
            "market_gap_rejected",
            "cannot_spend_other_reservation",
            "cancel_then_submit",
            "gap_take_profit",
            "equal_take_profit",
            "intrabar_ambiguous_stop",
            "equal_open_stop",
            "protection_uses_fill",
            "protection_step_rounding",
            "invalid_protection_rejects_entry",
            "disabled_protection",
            "buy_slippage_step",
            "sell_slippage_step",
            "minimum_fee_fractional",
            "weighted_cost_partial_exit",
            "protected_partial_exit",
            "protected_full_exit",
        }
        self.assertTrue(required <= {case["name"] for case in cases})
        for case in cases:
            with self.subTest(case=case["name"]):
                result = golden_result(case)
                expected = {
                    key.removeprefix("expected_"): value
                    for key, value in case.items()
                    if key.startswith("expected_")
                }
                self.assertEqual(set(result), set(expected))
                for key, value in result.items():
                    actual_expected = (
                        Decimal(expected[key]) if isinstance(value, Decimal) else expected[key]
                    )
                    self.assertEqual(value, actual_expected, key)


class TransactionFraming(unittest.TestCase):
    def records(self):
        first = {
            "batch_id": "batch-1",
            "batch_seq": 1,
            "first_event_seq": 1,
            "last_event_seq": 1,
            "previous_sha256": "0" * 64,
            "events": [{"type": "run.created"}],
        }
        second = {
            "batch_id": "batch-2",
            "batch_seq": 2,
            "first_event_seq": 2,
            "last_event_seq": 5,
            "previous_sha256": hashlib.sha256(canonical(first)).hexdigest(),
            "events": [
                {"type": "order.filled"},
                {"type": "cash.changed", "cash": "900"},
                {"type": "position.changed", "quantity": "1"},
                {"type": "protection.created"},
            ],
        }
        return first, second

    def test_every_byte_truncation_keeps_whole_transaction(self):
        first, second = self.records()
        prefix = transaction(first)
        record = transaction(second)
        for cut in range(len(record)):
            with self.subTest(cut=cut):
                self.assertEqual(recover(prefix + record[:cut]), [first])
        self.assertEqual(recover(prefix + record), [first, second])

    def test_corruption_does_not_skip_to_later_records(self):
        first, second = self.records()
        broken = transaction(first).replace(b"run.created", b"run.corrupt")
        with self.assertRaises(ContractError):
            recover(broken + transaction(second))

    def test_digest_chain_sequence_and_range(self):
        first, second = self.records()
        for field, value in (
            ("previous_sha256", "f" * 64),
            ("batch_seq", 4),
            ("first_event_seq", 3),
            ("last_event_seq", 6),
        ):
            changed = copy.deepcopy(second)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ContractError):
                recover(transaction(first) + transaction(changed))

    def test_float_in_transaction_rejected(self):
        with self.assertRaises(ContractError):
            transaction({"price": 0.1})

    def test_noncanonical_record_rejected(self):
        first, _ = self.records()
        with self.assertRaises(ContractError):
            recover(transaction(first).replace(b'"payload":', b'"payload": '))


if __name__ == "__main__":
    unittest.main()
