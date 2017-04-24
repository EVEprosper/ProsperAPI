# Developing ProsperAPI
We have worked very hard to make sure the process to release is as easy and trustworthy as possible.  Please use the following steps to be able to contribute to the project.

# 0. Get Your Environment In Order
Getting started is easy.  Set up a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) (remember python3).  Also, you will need `python3-dev` on linux systems.

> `git clone <ProsperAPI Address>`

> `cd ProsperAPI`

> `virtualenv venv -p python3`

> `source venv/bin/activate` (NOTE: windows is `venv\Scripts\activate`)

> `pip install -e . --extra-index-url=https://repo.fury.io/lockefox/` 

# 1. Debug Mode Work
_Humans Should Be Able To Touch Code_

The project is designed to run in a headless mode on nearly any machine.  Though there are some issues (mac cannot run fbprophet), the project is designed to make development easy.

> `python scripts/manager.py debug`

Do note that `scripts/app.cfg` is the tracked version of config.  You can fork a private version to `scripts/app_local.cfg` to be able to use secrets like passwords without committing them to git.

While in debug mode, Flask will refresh itself on every code update, though config updates may require restart.  

We suggest [postman](https://www.getpostman.com/) to debug http calls at `http://localhost:5000/`

# 2. Test Your Shit
_Testing Should Be Easy_

What is code without coverage?  [pytest](http://doc.pytest.org/en/latest/) hooks have been built-in to make testing easy.  Testing is just one command away:

>`python setup.py test`

Included in the test pass:
* unit testing
* coverage testing
* endpoint testing

## Write unit tests
Copious examples have been included for unit testing.  Be sure to exercise both expected `happypath` behavior along with expected failures.  Wrap unexpected/uncovered failures with `logging.error()` in the application, to send reports up to humans.

## Write endpoint tests
Though the [pytest-flask](http://pytest-flask.readthedocs.io/en/latest/) are not the greatest, examples have been included for testing endpoints, for more info look up [client_class](http://pytest-flask.readthedocs.io/en/latest/features.html#client-class-application-test-client-for-class-based-tests) tools for specific tests

## 2a: Travis-ci/coveralls
PR's will be checked automatically against Travis/Coveralls.  These tests are required to be green to merge.

* [Travis-CI](https://travis-ci.org/EVEprosper/ProsperAPI)
* [Coverall.io](https://coveralls.io/github/EVEprosper/ProsperAPI)

# 3. Build Your Shit
Once all tests are green and a candidate is ready to release, a build will need to be run.  This can be done on a test machine, but is the responsibilty of the deployer to run builds.  ((Build is not covered by CI))

It is suggested to install [Ubuntu16 x64](http://releases.ubuntu.com/16.04/) into a [virtualbox](https://www.virtualbox.org/wiki/Downloads) instance to run deployment testing.  

The next stage for release is to validate on a dummy box to make sure endpoints behave as expected.  Set up a virtualbox instance and test your branch there

Helpful configs
* Network settings: Bridge
* Don't forget to install virtualbox utilities from the CD prompt
* `python3-dev` required in the preinstall

Follow instructions from the [build](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/build.md) documentation and try to install.  Make sure the service(s) start, make sure the endpoints are reachable, use [postman](https://www.getpostman.com/) for manual validation.

# 4. Tag Your Shit
Don't forget to update `debian/changelog` for release and increment `setup.py` version information.  Tag the release on github for archiving.  Make sure a `.deb` file exists on the production box to roll back to.

# 5. Release Your Shit
Congrats!  Run the builder/installer on the production system, enjoy a strong drink!  
