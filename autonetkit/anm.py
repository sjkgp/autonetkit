#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

# TODO: rename duplicate use of logger var in log setup
class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return '[%s]: %s' % (self.extra['item'], msg), kwargs


class AutoNetkitException(Exception):
    pass
