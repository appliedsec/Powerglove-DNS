from datetime import datetime

import mock

from test import BasePowergloveTestCase
from powerglove_dns import model
from powerglove_dns.model import Record, Domain


class PowergloveModelTestCase(BasePowergloveTestCase):

    def setUp(self):

        super(PowergloveModelTestCase, self).setUp()
        datetime_patcher = mock.patch.object(
            model, 'datetime',
            mock.Mock(wraps=datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime(2013, 12, 11, 0, 0, 0)
        self.addCleanup(datetime_patcher.stop)

    def test_domain_incrementing_notified_serial_from_None(self):

        test = Domain(0, 'domain.name', notified_serial=None)
        self.assertIsNone(test.notified_serial)
        test.touch_serial()
        self.assertEqual(test.notified_serial, 2013121101)
        test.touch_serial()
        self.assertEqual(test.notified_serial, 2013121102)

    def test_domain_incrementing_notified_serial_from_yesterday(self):

        test = Domain(0, 'domain.name', notified_serial=2013121003)
        self.assertEqual(test.notified_serial, 2013121003)
        test.touch_serial()
        self.assertEqual(test.notified_serial, 2013121101)
        test.touch_serial()
        self.assertEqual(test.notified_serial, 2013121102)