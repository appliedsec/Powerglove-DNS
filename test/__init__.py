import logging
import logging.config
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import configobj

class PowergloveTestCase(unittest.TestCase):
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_settings.conf')

    @classmethod
    def setUpClass(cls):
        logging.config.fileConfig(cls.config_file)
        cls.log = logging.getLogger('%s.%s' % (cls.__module__, cls.__name__))
        cls.log.debug('test case initialized')
        cls.config = configobj.ConfigObj(cls.config_file)

    @classmethod
    def tearDownClass(cls):
        cls.log.debug('shutting down test case')
