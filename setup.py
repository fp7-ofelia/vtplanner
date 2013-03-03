#!/usr/bin/env python

import os
import sys
import glob

from setuptools import setup

setup(
    name='VTPlanner',
    version='1.0.0',
    url='https://github.com/fp7-ofelia/vtplanner',
    description='VT',
    author='Roberto Riggio',
    author_email='Roberto Riggio',
    license="LGPL",
    keywords="cli curses monitoring system",
    long_description=open('README').read(),
    packages=['vtplanner', 'vtplanner.backends', 'vtplanner.embedding'],
    entry_points={"console_scripts": ["vtplanner=vtplanner.vtplanner:main"]},
)
