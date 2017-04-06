[![Build Status](https://travis-ci.org/EVEprosper/ProsperAPI.svg?branch=master)](https://travis-ci.org/EVEprosper/ProsperAPI)
# ProsperAPI
A collection of API resources for the general public to leverage [EVE Prosper](http://www.eveprosper.com/)'s [EVE Online](https://www.eveonline.com/) market data.

These services are designed to be easy to deploy and maintain for any member of the community.  Though some private resources will require data from our master host, this [Flask-Restful](https://flask-restful.readthedocs.io/en/0.3.5/) project _should be easy to distribute_.  

# Getting Started
Though testing/developent is platform agnostic, the following resources are required for production:

* Debian Linux (Ubuntu16)
* Python >3.5
* [dh-virtualenv](https://dh-virtualenv.readthedocs.io/en/1.0/) >1.0
* Access to [Prosper GemFury](https://repo.fury.io/lockefox/)

## For Developers
Getting started is easy for developers.  Just spin up a [virtualenv](https://python-docs.readthedocs.io/en/latest/dev/virtualenvs.html) and install
> `pip install .`

Testing is designed to be easy too!  Just run tests from setup.py
> `python setup.py test`

**NOTES**
* On Windows, numerical libraries are touchy.  Have included manually compiled wheels in project
* [fbprophet](https://github.com/facebookincubator/prophet) is a complicated dedpendency.  See build docs for more notes
* Mac is special, [fbprophet](https://github.com/facebookincubator/prophet) is not supported, but everything else is

## For Sysadmins
Please refer to our [build documentation](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/build.md) for step by step

# What Is Offered
## PublicAPI - Transformative API Endpoints
All endpoints provided in `publicAPI` are open and require no special databases.  

* [OHLC](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#ohlc): transform in-game history feed into a traditional OHLC format
* [Prophet](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#prophet): provide forecasts on future prices, given previous history

# Legal Stuff
EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf. CCP hf. has granted permission to EVE-Prosper and John Purcell to use EVE Online and all associated logos and designs for promotional and information purposes on its website but does not endorse, and is not in any way affiliated with, EVE-Prosper. CCP is in no way responsible for the content on or functioning of this website, nor can it be liable for any damage arising from the use of this website.
