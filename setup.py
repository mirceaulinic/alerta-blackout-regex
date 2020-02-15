#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
'''
import codecs
from setuptools import setup, find_packages

__author__ = 'Mircea Ulinic <ping@mirceaulinic.net>'

with codecs.open('README.rst', 'r', encoding='utf8') as file:
    long_description = file.read()

setup(
    name='alerta-blackout-regex',
    version='1.0.0rc1',
    author='Mircea Ulinic',
    author_email='ping@mirceaulinic.net',
    py_modules=['blackout_regex'],
    description='Alerta Blackout enhancement plugin',
    long_description=long_description,
    include_package_data=True,
    zip_safe=True,
    url='https://github.com/mirceaulinic/alerta-blackout-regex',
    license="Apache License 2.0",
)
