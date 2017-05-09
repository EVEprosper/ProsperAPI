# Stock Splits
_Because Lockefox is an idiot and made the project no-db_

So, they announced [PLEX was going to be split](https://community.eveonline.com/news/dev-blogs/plex-changes-on-the-way/).  NBD, right?  Because ProsperAPI has no backing database, this is actually more difficult than it should be.

# Declaring A Split

```javascript
publicAPI/split_info.json
[
	
	{
		"type_id": ,		#which item
		"type_name": ,		#type name for debug
		"original_id": , 	#ID before the split
		"new_id": , 		#ID after the split
		"split_date": ,		#%Y-%m-%d of split
		"bool_mult_div": , 	#price multiplied by split?
		"split_rate": ,		#new quantity
	}
]
```

Split info is designed to work in pairs.  Define both old and new items in paired splits for backwards-compatability.

Also can be used with a `"split_rate": 1` for a `type_id` remapping.

# Backloading cache data
Because [Prophet](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#prophet) requires 720 days of back history, we need to keep an archive in-project to keep expected quality of service.  Also, though CCP has said ESI will allow some back-compat, [EVE-Marketdata](https://eve-marketdata.com/) makes no such promises.

To backload:
> `python scripts/create_splitcache.py`

See `-h` for settings for switching source, type, filename, regions, etc

Don't forget to commit updates ;)

# Testing
Test suite uses a hacky sideload that uses Tritanium (34) and Pyerite (35) to validate behavior.  

Also, `.travis.yml` creates a local split_cache.json file just for automated testing.  See `.travis.yml` for preparing [test environment](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/release.md#2-test-your-shit).

# Database Note:
Splitcache has purposefully been made to run in a flat-file, rather than use [tinymongo](https://github.com/schapman1974/tinymongo) for remote database connection compatability.  This was done to continue the spirit of "anyone can launch ProsperAPI anywhere".