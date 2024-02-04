#!/usr/bin/env python

"""
Simple module wrapper to load settings file in order
to have it available in all modules.
"""
import yaml
import os


#settings_filename = os.path.join(os.path.dirname(__file__), 'settings.yaml')
#settings_filename = '../'
#settings_filename = '/tmp/settings.yaml'
settings_filename = './medknow/settings.yaml'
with open(settings_filename, "r") as f:
    settings = yaml.load(f)
