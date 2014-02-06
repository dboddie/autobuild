#!/usr/bin/env python

from distutils.core import setup

setup(
    name="autobuild",
    description="Tools for building Debian packages from source code repositories.",
    author="David Boddie",
    author_email="david.boddie@met.no",
    url="http://www.met.no/",
    version="0.1.0",
    packages=["autobuild"],
    scripts=["autobuild-builder.py",
             "autobuild-repo.py",
             "autobuild-www.cgi"]
    )
