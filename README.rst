ProsperAPI
==========

|Build Status| |Coverage Status|

A collection of API resources for the general public to leverage `EVE
Prosper`_\ ’s `EVE Online`_ market data.

These services are designed to be easy to deploy and maintain for any
member of the community. Though some private resources will require data
from our master host, this `Flask-Restful`_ project *should be easy to
distribute*.

Getting Started
===============

Though testing/developent is platform agnostic, the following resources
are required for production:

-  Debian Linux (Ubuntu16)
-  Python >3.5
-  `dh-virtualenv`_ >1.0

For Developers
--------------

Getting started is easy for developers. Just spin up a `virtualenv`_ and
install

    ``pip install . --extra-index-url=https://repo.fury.io/lockefox/``

Testing is designed to be easy too! Just run tests from setup.py

    ``python setup.py test``

**NOTES**

-  On Windows, numerical libraries are touchy. Have included manually
   compiled wheels in project
-  `fbprophet`_ is a complicated dedpendency. See `build documentation`_ for more
   notes
-  Mac is special, `fbprophet`_ is not supported, but everything else is

For Sysadmins
-------------

Please refer to our `build documentation`_ for step by step

What Is Offered
===============

PublicAPI - Transformative API Endpoints
----------------------------------------

All endpoints provided in ``publicAPI`` are open and require no special
databases.

-  `OHLC`_: transform in-game history feed into a traditional OHLC
   format
-  `Prophet`_: provide forecasts on future prices, given previous
   history

Legal Stuff
===========

EVE Online and the EVE logo are the registered trademarks of CCP hf. All
rights are reserved worldwide. All other trademarks are the property of
their respective owners. EVE Online, the EVE logo, EVE and all
associated logos and designs are the intellectual property of CCP hf.
All artwork, screenshots, characters, vehicles, storylines, world facts
or other recognizable features of the intellectual property relating to
these trademarks are likewise the intellectual property of CCP hf. CCP
hf. has granted permission to EVE-Prosper and John Purcell to use EVE
Online and all associated logos and designs for promotional and
information purposes on its website but does not endorse, and is not in
any way affiliated with, EVE-Prosper. CCP is in no way responsible for
the content on or functioning of this website, nor can it be liable for
any damage arising from the use of this websi

.. _EVE Prosper: http://www.eveprosper.com/
.. _EVE Online: https://www.eveonline.com/
.. _Flask-Restful: https://flask-restful.readthedocs.io/en/0.3.5/
.. _dh-virtualenv: https://dh-virtualenv.readthedocs.io/en/1.0/
.. _virtualenv: https://python-docs.readthedocs.io/en/latest/dev/virtualenvs.html
.. _fbprophet: https://github.com/facebookincubator/prophet
.. _build documentation: https://github.com/EVEprosper/ProsperAPI/blob/master/docs/build.md
.. _OHLC: https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#ohlc
.. _Prophet: https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#prophet

.. |Build Status| image:: https://travis-ci.org/EVEprosper/ProsperAPI.svg?branch=master
   :target: https://travis-ci.org/EVEprosper/ProsperAPI
.. |Coverage Status| image:: https://coveralls.io/repos/github/EVEprosper/ProsperAPI/badge.svg?branch=master
   :target: https://coveralls.io/github/EVEprosper/ProsperAPI?branch=master

