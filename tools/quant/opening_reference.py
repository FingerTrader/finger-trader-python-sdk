"""P0 opening-only accounting oracle for frozen hand-calculated examples.

No event loop, OHLC path simulation, callbacks, I/O, fees or slippage engine.
Deliberately refuses models outside these zero-fee/zero-slippage fixtures.
P3 must consume the same inputs/expected snapshots with its production engine.
"""

import copy
from decimal import Decimal, localcontext


def opening_result(case, policy):
    with localcontext() as ctx:
        ctx.prec = 34
        return _opening(case, policy)


def _opening(case, policy):
    if case["fee_rate"] != "0" or case["slippage_bps"] != "0":
        raise ValueError("P0 opening reference supports zero fees/slippage only")
    orders = copy.deepcopy(case["orders"])
    groups = copy.deepcopy(case["groups"])
    cash = Decimal(case["initial"]["cash"])
    quantity = Decimal(case["initial"]["quantity"])
    cost = Decimal(case["initial"]["position_cost"])
    realized = Decimal("0")
    price = Decimal(case["bar"]["open"])
    fills = []
    steps = []
    priority = {kind: i for i, kind in enumerate(policy["opening_priority"])}
    if len({o["submit_seq"] for o in orders}) != len(orders):
        raise ValueError("duplicate submission sequence")
    if len({o["order_id"] for o in orders}) != len(orders):
        raise ValueError("duplicate order ID")
    for order in orders:
        if order["kind"] not in priority or order["side"] not in ("buy", "sell"):
            raise ValueError("unsupported fixture order")
        for value, step in (
            (Decimal(order["quantity"]), Decimal(case["product"]["quantity_step"])),
            (price, Decimal(case["product"]["price_step"])),
        ):
            if value <= 0 or value % step:
                raise ValueError("invalid fixture product precision")

    def text(value):
        return format(value, "f")

    def snapshot():
        reserved_cash = sum(Decimal(o["reserved_cash"]) for o in orders)
        reserved_quantity = sum(Decimal(o["reserved_quantity"]) for o in orders)
        reserved_quantity += sum(Decimal(g["quantity"]) for g in groups if g["status"] == "active")
        if not (cash >= reserved_cash >= 0 and quantity >= reserved_quantity >= 0 and cost >= 0):
            raise ValueError("opening ledger reservation invariant")
        return {
            "cash": text(cash),
            "reserved_cash": text(reserved_cash),
            "available_cash": text(cash - reserved_cash),
            "quantity": text(quantity),
            "reserved_quantity": text(reserved_quantity),
            "available_quantity": text(quantity - reserved_quantity),
            "position_cost": text(cost),
            "realized_pnl": text(realized),
            "orders": {
                o["order_id"]: {k: o[k] for k in ("status", "reserved_cash", "reserved_quantity")}
                for o in orders
            },
            "groups": {g["group_id"]: {k: g[k] for k in ("status", "quantity")} for g in groups},
            "fills": copy.deepcopy(fills),
        }

    initial = snapshot()

    def process(order, stage):
        nonlocal cash, quantity, cost, realized
        if order["status"] != "accepted":
            outcome = "ignored_terminal"
        else:
            qty = Decimal(order["quantity"])
            debit = price * qty
            state = snapshot()
            if order["side"] == "buy" and debit > (
                Decimal(order["reserved_cash"]) + Decimal(state["available_cash"])
            ):
                order["status"] = "rejected"
                outcome = "INSUFFICIENT_CASH"
            else:
                if order["side"] == "buy":
                    cash -= debit
                    quantity += qty
                    cost += debit
                else:
                    group = next(
                        (g for g in groups if g["group_id"] == order.get("group_id")), None
                    )
                    available = (
                        Decimal(group["quantity"])
                        if group
                        else (
                            Decimal(order["reserved_quantity"])
                            + Decimal(state["available_quantity"])
                        )
                    )
                    if qty > available or qty > quantity:
                        raise ValueError("invalid preaccepted fixture sell reservation")
                    allocation = cost if qty == quantity else cost * qty / quantity
                    cash += debit
                    quantity -= qty
                    cost -= allocation
                    realized += debit - allocation
                    if group:
                        group["quantity"] = "0"
                        group["status"] = "closed"
                        for sibling in orders:
                            if (
                                sibling is not order
                                and sibling.get("group_id") == group["group_id"]
                            ):
                                sibling["status"] = "cancelled"
                                sibling["reserved_cash"] = sibling["reserved_quantity"] = "0"
                order["status"] = "filled"
                fills.append(
                    {
                        "order_id": order["order_id"],
                        "side": order["side"],
                        "quantity": text(qty),
                        "price": text(price),
                        "fee": "0",
                    }
                )
                outcome = "FILLED"
            order["reserved_cash"] = order["reserved_quantity"] = "0"
        steps.append(
            {"stage": stage, "order_id": order["order_id"], "outcome": outcome, "state": snapshot()}
        )

    def executable(order):
        if order["kind"] == "market":
            return True
        if order["kind"] == "protective_stop":
            return price <= Decimal(order["stop_price"])
        limit = Decimal(order["limit_price"])
        return price <= limit if order["side"] == "buy" else price >= limit

    # Sort all candidates once; recheck terminal/OCO/resource state per operation.
    for order in sorted(orders, key=lambda o: (priority[o["kind"]], o["submit_seq"])):
        if executable(order):
            process(order, "open")
    for order_id in case["terminal_probes"]:
        order = next(o for o in orders if o["order_id"] == order_id)
        if order["status"] not in ("cancelled", "filled", "rejected"):
            raise ValueError("terminal probe must not simulate a new intrabar path")
        process(order, "terminal_probe")
    return {"initial": initial, "steps": steps, "final": snapshot()}
