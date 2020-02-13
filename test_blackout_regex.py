import sys
import unittest

from alertaclient.models.blackout import Blackout

from mock import Mock, MagicMock, patch, call
app_mock = sys.modules['alerta.app'] = Mock()

import blackout_regex
from blackout_regex import BlackoutRegex

blackouts = [
    Blackout(
        environment='test',
        resource='test\d',
    ),
    Blackout(
        environment='test',
        service='test-service\d',
    ),
    Blackout(
        environment='test',
        tags=[
            'site=par.*'
        ]
    ),
    Blackout(
        environment='test',
        tags=[
            'site=par.*',
            'role=router'
        ]
    )
]


blackout_regex.PluginBase = Mock


class TestEnhance(unittest.TestCase):

    @patch('blackout_regex.Client', return_value=Mock())
    def test_new_alert_no_match(self, alerta_client):
        '''
        Test alert not matching a regex blackout.
        '''
        alerta_client.return_value.get_blackouts.return_value = blackouts
        alert = Mock(
            resource='test::resource',
            tags=[],
            service=['test-service'],
            event='test-event',
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(alert.status, 'open')
        self.assertEqual(alert.tags, [])
