# Building Prosper API
To help deploy Prosper API services, a .deb builder/installer has been developed

# Notes

(need to figure out something for the prosperAPI_local.cfg)

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
* dpkg
* [dh-virtualenv](http://dh-virtualenv.readthedocs.io/en/latest/index.html)

## Building the Package

1. `sudo apt-get install dpkg`
2. `sudo apt-get install dh-virtualenv`
3. `sudo apt-get install debhelper`
4. `sudo apt-get install python3-pip`
5. `sudo pip3 install wheel`
6. `sudo pip3 install setuptools`
7. `sudo dpkg-buildpackage -us -uc`

# How to Install

