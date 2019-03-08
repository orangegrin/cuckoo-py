from enum import Enum, unique


class Side(Enum):
    Buy = "Buy"
    Sell = "Sell"


class OrderType(Enum):
    Limit = "Limit"
    Market = "Market"


class OrderResultType(Enum):
    Unknown = "Unknown"
    Filled = "Filled"
    FilledPartially = "FilledPartially"
    Pending = "Pending"
    Error = "Error"
    Canceled = "Canceled "
    PendingCancel = "PendingCancel"