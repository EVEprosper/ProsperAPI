# CREST APIs
As a public service, we provide some tools for transforming and extending EVE Online's [CREST API](http://eveonline-third-party-documentation.readthedocs.io/en/latest/crest/index.html).  This project is an exercise in Flask and REST design/deployment.

### Note:
As of writing this (2017-03-10), CCP is working to replace CREST/XML API's with [ESI](https://esi.tech.ccp.is/latest/).  We will review replacing the CREST request structure with an ESI one, but worry about ESI/oAuth scoping for a reasonably simple app.

# Endpoints
## OHLC
|  |  |
| --- | --- |
| **Path** | /api/OHLC.*\<return_format\>* (csv, json) |
| **Methods** | GET |
| **Args** | `typeID` <br /> `regionID` <br /> `api` (unused) |
| **Headers** | User-Agent |
| **Returns** | [`date`, `open`, `high`, `low`, `close`, `volume`] |

OHLC endpoint transposes the [market history endpoint](http://eveonline-third-party-documentation.readthedocs.io/en/latest/crest/eve/eve_market.html#market-history) into [OHLC format](http://www.phplot.com/phplotdocs/ex-ohlcbasic.html).  This should work in most existing TA tools as-is.  Currently powering charting at [EVE Mogul](https://www.eve-mogul.com/)

**NOTES**

* RTT is not excellent.  Validates against CREST for `typeID` and `regionID`. 
    * Does have cache layer, but new ID`s will take ~3-5s to resolve
* Request throughput is poor.  Total traffic capacity is single-thread
* OHLC calc is a hack.  Uses "today" as `close` and transposes "yesterday's" price as `open`
* API feature not used.  Internal API keying to filter users

## prophet
|  |  |
| --- | --- |
| **Path** | /api/prophet.*\<return_format\>* (csv, json) |
| **Methods** | GET |
| **Args** | `typeID` <br /> `regionID` <br /> `api` <br /> `range` optional |
| **Headers** | User-Agent |
| **Returns** | [`date`, `avgPrice`, `yhat`, `yhat_low`, `yhat_high`, `prediction`] |

Prophet endpoint uses [Prophet](https://facebookincubator.github.io/prophet/) forecasting library to predict future price fluctuations.  Combining [Prosper's](http://www.eveprosper.com) archive of EVE's [market history endpoint](http://eveonline-third-party-documentation.readthedocs.io/en/latest/crest/eve/eve_market.html#market-history) we generate a best-guess for future prices.  Currently powering charting at [EVE Mogul](https://www.eve-mogul.com/)

More info on forecasts can be found on [our blog](https://eve-prosper.blogspot.com/2017/03/aspiring-hari-seldon-part-2.html)

**NOTES**

* **VERY NAIVE FORECASTING**.  This is a science experiment, not a fool-proof forecast of future events
* Does not understand CCP dev cycle.  Will approximate cycles with [changepoint prediction](https://facebookincubator.github.io/prophet/docs/trend_changepoints.html) but only uses requested item to guess cycles
* **PROVIDED WITHOUT WARANTY**.  *Seriously, don't trade what you can't afford to lose, this thing is just a cartoon, don't go all Russian on my house*
