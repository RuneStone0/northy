# Saxo Config
All config values are case sensitive.

## `OrderPreference`
`OrderPreference` controls the order type to use when entering a new trade.
* `Market` *(default)* will enter the trade at the market price. This is the
fastest way to enter a trade, but you might get a worse price than the signal.
* `Limit` will enter the trade at a specific price. This is slower than market
orders, but you will get the price you want. The tradeoff is that you might not
get filled if the price doesn't reach your limit price.

## `EntryStoploss` NOT IMPLEMENTED
`EntryStoploss` controls the SL to set when entering a new trade. If `ordertype`
is set to `market`. We will most likely get a different entry price than what 
was given by a signal. E.g. if signal entry at 100, but the actual entry was at 
105 you need to decide if where to put the stoploss and consider the tradeoffs.

* `SignalEntry` *(default)* sets stop loss at x points away from the signal 
entry price. This is slightly more risk on a per-trade basis. The benefit of 
this, is that you're guranteed to be apart of all trade 
* `ActualEntry` sets stop loss at x points away from the entry price. This is 
less risky on a per-trade basis. The trade off is that, you risk getting 
stopped out and will not get a re-entry signal, and thus risking missing the entire 
trade.

## `flatstop` NOT IMPLEMENTED
This setting is tightly coupled with the `EntryStoploss` setting. Consider both 
settings carefully and risk and trading behaviour vary.
* `Ignore` will ignore all FLATSTOP signals and keep existing SL. This ensures 
you won't get stopped out early. But also increase your per-trade basis risk.
This is needed, if you want to be more aggressive. For example, when a signal
enters at 100, but you're using market orders and the actual entry is at 105.
If price moves to 103 and you already have a stoploss at 100, you will get
stopped out. If you ignore the FLATSTOP signal, you will not get stopped out.
* `AtEntry`
* 
