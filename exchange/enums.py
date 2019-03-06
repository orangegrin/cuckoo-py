from enum import Enum, unique


class Side(Enum):
    Buy = 0
    Sell = 1


class OrderType(Enum):
    Limit = 0
    Market = 1


class OrderResultType(Enum):
    Unknown = 0
    Filled = 1
    FilledPartially = 2
    Pending = 3
    Error = 4
    Canceled = 5
    PendingCancel = 6

