""" Common order types with reusable parameter configurations."""
import sys
sys.path.append("site-packages")

from ib_insync import (
    Order,
    LimitOrder,
)

from dataclasses import dataclass

from typing import *

# Note: all functions should have params in the same order!

# Order field details:
# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html


@dataclass
class IOrder:
    """A wrapper class to help organize the common order logic we want to reuse.

    This looks a bit weird because we are basically duplicating most of the Order
    fields ourself and populating them before passing them back to Order, but this
    allows us to basically generate one abstract Order request then pull out more
    specific concrete Order types with conditions/algos as needed via encapsulating
    the meta-order logic inside methods generating the actual final Order object.
    Individual field detail meanings are at:
    https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
    """

    action: Literal["BUY", "SELL"]

    qty: float

    # basic limit price
    lmt: float = 0.00

    # specify amount as spend value instead of shares or contracts
    qtycash: float = 0.00

    # aux holds anything not a limit price and not a trailing percentage:
    #   - stop price for stop / stop limita / stop with protection
    #   - trailing amounts for trailing orders (instead of .trailingPercent)
    #   - touch price on MIT
    #   - offset for pegs (treated as (bid + aux) for sell and (ask - off) for buys)
    #   - trigger price for LIT (Same as touch for MIT, when the "IT" becomes marketable)

    # Note: IBKR gives a warning (but not a hard error) if assigning GTC to options.
    tif: Literal["GTC", "IOC", "FOK", "OPG", "GTD", "DAY", "Minutes"] = "GTC"

    # If set to true, allows orders to also trigger or fill outside of regular trading hours.
    outsiderth: bool = True

    # preview
    whatif: bool = False

    trailpct: int = 0
    trailstop: float = 0.00
    lmtPriceOffset: float = 0.00
    aux: float = 0.00


    def order(self, orderType: str) -> Order:
        """Return a specific Order object by name."""
        omap = {
            "MKT": self.market,
            "LMT": self.limit,
            "TRAIL LIMIT": self.trailingStopLimit,
            "TRAIL": self.trailingStop
        }

        return omap[orderType]()


    def commonArgs(self, override: dict[str, Any] = None) -> dict[str, Any]:
        common = dict(
            tif=self.tif,
            outsideRth=True,
            whatIf=self.whatif,
        )

        if override:
            common.update(override)

        return common


    def adjustForCashQuantity(self, o):
        """Check if we need to use cash instead of direct quantity.

        IBKR API allows order size as cash value optionally.
        So we check if the inbound quantity is a string starting with
        a currency spec, then use cash quantity instead of share/contract
        quantity."""

        if isinstance(self.qty, str) and self.qty.startswith("$"):
            cashqty = float(self.qty[1:])
            o.totalQuantity = 0
            o.cashQty = cashqty


    def limit(self) -> LimitOrder:
        o = LimitOrder(
            self.action,
            self.qty,
            self.lmt,
            **self.commonArgs(),
        )

        self.adjustForCashQuantity(o)
        return o


    def trailingStopLimit(self) -> Order:
        # if self.aux and self.trailpct:
        #     raise Exception("Can't specify both Aux and Trailing Percent!")

        # # Exclusive, can't have both:
        # #    auxPrice=self.aux, # TRAILING AMOUNT IN DOLLARS
        # #    trailingPercent=self.trailingPercent # TRAILING AMOUNT IN PERCENT
        # if self.aux:
        #     whichTrail = dict(auxPrice=self.aux)
        # else:
        #     whichTrail = dict(trailingPercent=self.trailpct)

        o = Order(
            action=self.action,
            totalQuantity=self.qty,
            lmtPriceOffset=self.lmtPriceOffset,  # HOW FAR DOWN TO START THE LIMIT ± AGAINST CURRENT PRICE (- sell, + buy)
            # trailStopPrice=self.trailstop,  # IF NO UP MOVEMENT, WHEN TO TRIGGER ORDER <-- THIS IS WHAT "TRAILS"
            # trailingPercent=self.trailpct,
            orderType="TRAIL LIMIT",
            auxPrice = self.aux,
            # **whichTrail,  # type: ignore
            **self.commonArgs(),  # type: ignore
        )

        self.adjustForCashQuantity(o)
        return o


    def market(self) -> Order:
        o = Order(
            action=self.action,
            totalQuantity=self.qty,
            orderType="MKT",
            **self.commonArgs(),
        )

        self.adjustForCashQuantity(o)
        return o

    
    def trailingStop(self) -> Order:
        # if self.aux and self.trailpct:
        #     raise Exception("Can't specify both Aux and Trailing Percent!")

        # Exclusive, can't have both:
        #    auxPrice=self.aux, # TRAILING AMOUNT IN DOLLARS
        #    trailingPercent=self.trailingPercent # TRAILING AMOUNT IN PERCENT
        # if self.aux:
        #     whichTrail = dict(auxPrice=self.aux)
        # else:
        #     whichTrail = dict(trailingPercent=self.trailpct)

        o = Order(
            action=self.action,
            totalQuantity=self.qty,
            trailingPercent=self.trailpct,
            # lmtPriceOffset=self.lmtPriceOffset,  # HOW FAR DOWN TO START THE LIMIT ± AGAINST CURRENT PRICE (- sell, + buy)
            trailStopPrice=self.trailstop,  # IF NO UP MOVEMENT, WHEN TO TRIGGER ORDER <-- THIS IS WHAT "TRAILS"
            orderType="TRAIL",
            # **whichTrail,  # type: ignore
            **self.commonArgs(),  # type: ignore
        )

        self.adjustForCashQuantity(o)
        return o
