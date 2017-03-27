# Releasing ProsperAPI
To maintain quality, and lower pain later down the road, the following release procedure is recommended

# 0. Get your enviroment in order
Getting started is easy.  Set up a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (remember python3).  Also, you will need `python3-dev` on linux systems.

> `pip install . --extra-index-url=https://repo.fury.io/lockefox/`

Please keep test and prod dependencies separate with `test_requires` and `package_requires`

# 1. Test Your Shit
_Testing should be easy_

[pytest](http://doc.pytest.org/en/latest/) hooks have been built-in to make testing easy.  Testing is just one command away:

>`python setup.py test`

Included in the test pass:
* unit testing
* coverage testing
* endpoint testing

## Write unit tests
Copious examples have been included for unit testing.  Be sure to exercise both expected `happypath` behavior along with expected failures.  Wrap unexpected/uncovered failures with `logging.error()` in the application, to send reports up to humans.

## Write endpoint tests
Though the [pytest-flask](http://pytest-flask.readthedocs.io/en/latest/) are not the greatest, examples have been included for testing endpoints, for more info look up [client_class](http://pytest-flask.readthedocs.io/en/latest/features.html#client-class-application-test-client-for-class-based-tests) tools for specific tests

# 2. Build And Test Your Shit
It is suggested to install [Ubuntu16 x64](http://releases.ubuntu.com/16.04/) into a [virtualbox](https://www.virtualbox.org/wiki/Downloads) instance to run deployment testing.  

The next stage for release is to validate on a dummy box to make sure endpoints behave as expected.  Set up a virtualbox instance and test your branch there

Helpful configs
* Network settings: Bridge
* Don't forget to install virtualbox utilities from the CD prompt
* `python3-dev` required in the preinstall

Follow instructions from the [build](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/build.md) documentation and try to install.  Make sure the service(s) start, make sure the endpoints are reachable, use [postman](https://www.getpostman.com/) for manual validation.

# 3. Tag Your Shit
Don't forget to update `debian/changelog` for release and increment `setup.py` version information.  Tag the release on github for archiving.  Make sure a `.deb` file exists on the production box to roll back to.

# 4. Release Your Shit
Congrats!  Run the builder/installer on the production system, enjoy a strong drink!  
