# Building Prosper API
To help deploy Prosper API services, a .deb builder/installer has been developed

# Notes

### [fbprophet](https://facebookincubator.github.io/prophet/docs/installation.html)
[Prophet](https://facebookincubator.github.io/prophet/docs/installation.html) is a troublesome library to install.  Required build-from-source to get working with dh-virtualenv.  

Best-practice may be to host precompiled binary on a private PyPI service (GemFury, DevPi)

```
git clone --recursive https://github.com/stan-dev/pystan.git
cd pystan
python setup.py install
pip install matplotlib #for png.h and freetype.h 
cd ..
git clone https://github.com/facebookincubator/prophet.git
cd prophet/python
python setup.py install
```

Additionally, for windows, required [VS2015 C++ binaries](http://landinghub.visualstudio.com/visual-cpp-build-tools) and to build from source.  See `wheels/` for precompiled windows packages.  Also, Prophet will not work on mac systems.

### API Keys
The [Prophet](https://github.com/EVEprosper/ProsperAPI/blob/master/docs/crest_endpoint.md#prophet) endpoint relies on API keys to gate access.  Roll new ones for users with `scripts/manage_api.py` and don't forget to back up `publicAPI/cache/apikeys.json` for best results.

The build will automatically snatch up the new keys and build them into its installer.  **DO BACKUP -- INSTALLER WILL SMASH RELEASED APIKEYS.JSON FILE ON INSTALL**

### Discord Monitoring
```
[LOGGING]
   discord_webhook = #SECRET
```
Configure the `discord_webhook` value in `scripts/app.cfg` to enable [Discord Logging](https://github.com/EVEprosper/ProsperCommon/blob/master/docs/prosper_logging.md#configure_discord_logger).  Service has already been built-in with python logging handlers to help alert if/when something goes catastrophically wrong.  

# How To Build
ProsperAPI is set up to use [dh-virtualenv](http://dh-virtualenv.readthedocs.io/en/latest/index.html).  This should wrap up the project into a .deb file for easy installing/deploying

## Prereqs
* Debian system (tested on Ubuntu 16)
* Python 3.x (developed for Python 3.5)
* pip packages
    * wheel
    * setuptools
    * virtualenv
    * [Plumbum](https://plumbum.readthedocs.io/en/latest/)
    * matplotlib
    * pystan
    * fbprophet
* dpkg
* [dh-virtualenv](http://dh-virtualenv.readthedocs.io/en/latest/index.html) v1.0

## Building the Package

1. `sudo apt-get install dpkg`
2. `sudo apt-get install dh-virtualenv`
3. `sudo apt-get install debhelper`
4. `sudo apt-get install python3-pip`
5. `sudo pip3 install wheel`
6. `sudo pip3 install setuptools`
7. see notes about build-from-source for fbprophet
7. `sudo dpkg-buildpackage -us -uc`

# How to Install

1. `sudo dpkg -i prosper-api_[version]_amd64.deb
2. `sudo systemctl status crest_endpoint.service` to  make sure deploy is correct

## Notes
Deploys a virgin virtualenv for code to run in.  Does not adjust production python on machine.

`source /opt/venvs/prosper-api/bin/activate`
`sudo /opt/venvs/prosper-api/bin/python` <-- for running python directly
