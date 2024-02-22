# Signal
Alert Tweets are parsed and converted into a structured format. For example, the following tweet: 

> `ALERT: Closed 2nd scale $NDX`
> 
> `IN 13720 OUT: 12484 +1236`

will be converted into the following signal:

> `SPX_SCALEOUT_IN_13720_OUT_12484_POINTS_1236`

The signal is then processed by the trading engine.

## Format
```
Schema:
    {TICKER}_{ACTION}_{DIRECTION}_IN_{PRICE}_OUT_{PRICE}_SL_{POINTS}
    TICKER_ACTION_DIRECTION_IN_PRICE_OUT_PRICE_SL_POINTS

Breakdown
    TICKER - the ticker code e.g. SPX
    ACTION - the action to take on a signal
        TRADE       - enter new trade, based on direction we either go long / short
        FLAT        - adjust stop loss to break even
        FLATSTOP    - stop loss was triggered, this is just an observation, no action needed
        CLOSED      - close recently opened position (100% of position)
        SCALEOUT    - scale out of position (25% of position)
        LIMIT       - set a limit order
    DIRECTION - define the position direction
        LONG        - go long a trade (buy)
        SHORT       - go short a trade (sell)
    PRICE - the price at which the signal was entered
    SL - the number of points from which to set the stop loss
```

## Examples
```
SPX_TRADE_LONG_IN_13720_OUT_12484_SL_1236
SPX_TRADE_SHORT_IN_13720_OUT_12484_SL_1236
NDX_FLAT
SPX_FLATSTOP
SPX_CLOSED
SPX_SCALEOUT_IN_3588_OUT_3682_POINTS_94
SPX_LIMIT_LONG_IN_3673_OUT_3663_SL_10
```

## JSON Schema
```json
{
  "type": "object",
  "properties": {
    "TICKER": { "type": "string" },
    "ACTION": { "type": "string", "enum": ["TRADE", "FLAT", "FLATSTOP", "CLOSED", "SCALEOUT", "LIMIT", "STOPLOSS"] },
    "DIRECTION": { "type": "string", "enum": ["LONG", "SHORT"] },
    "IN_PRICE": { "type": "number" },
    "OUT_PRICE": { "type": "number" },
    "SL_POINTS": { "type": "number" }
  },
  "required": ["TICKER", "ACTION", "DIRECTION", "IN_PRICE", "OUT_PRICE", "SL_POINTS"],
  "additionalProperties": false
}
```

## JSON Example
`ALERT: Flat stopped $SPX Re-entry short IN 4770 - 10 pt stop`

```json
[
    {
        "TICKER": "SPX",
        "ACTION": "FLATSTOP",
    },
    {
    "TICKER": "SPX",
    "ACTION": "TRADE",
    "DIRECTION": "SHORT",
    "IN_PRICE": 4770,
    "SL_POINTS": 10
    }
]
```
  "properties": {
    "TICKER": { "type": "string" },
    "ACTION": { "type": "string", "enum": ["TRADE", "FLAT", "FLATSTOP", "CLOSED", "SCALEOUT", "LIMIT", "STOPLOSS"] },
    "DIRECTION": { "type": "string", "enum": ["LONG", "SHORT"] },
    "IN_PRICE": { "type": "number" },
    "OUT_PRICE": { "type": "number" },
    "SL_POINTS": { "type": "number" }
  },
  "required": ["TICKER", "ACTION", "DIRECTION", "IN_PRICE", "OUT_PRICE", "SL_POINTS"],
  "additionalProperties": false
}
```

