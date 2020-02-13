# -*- coding: utf-8 -*-
import sys
import logging
import unittest

from alertaclient.models.alert import Alert
from alertaclient.models.blackout import Blackout

from mock import Mock

client_mod = sys.modules['alertaclient.api'] = Mock()
client_mod.Client = Mock()

plugins_mod = sys.modules['alerta.plugins'] = Mock()
plugins_mod.PluginBase = Mock

client_mod.Client.return_value.get_blackouts.return_value = [
    Blackout(
        environment='test',
        resource='test\d',
        duration=3600,
        id='1'
    ),
    Blackout(
        environment='test',
        service='service-([a-zA-Z])',
        duration=3600,
        id='2',
    ),
    Blackout(
        environment='test',
        tags=[
            'site=site.*'
        ],
        duration=3600,
        id='3',
    ),
    Blackout(
        environment='test',
        tags=[
            'site=site.*',
            'role=router'
        ],
        duration=3600,
        id='4'
    )
]

import blackout_regex
from blackout_regex import BlackoutRegex

log = logging.getLogger(__name__)


class TestEnhance(unittest.TestCase):

    def test_new_alert_no_match(self):
        '''
        Test alert not matching a regex blackout.
        '''
        alert = Alert(
            id='no-match',
            resource='test::resource',
            event='test-event',
            service=['test-service'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(test.status, 'open')
        self.assertEqual(test.tags, [])

    def test_new_alert_match_resource(self):
        '''
        Test alert matching a regex blackout on the resource field.
        '''
        alert = Alert(
            id='match-resource',
            resource='test1',
            event='test-event',
            service=['test-service'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['regex_blackout=1'])

    def test_new_alert_match_service(self):
        '''
        Test alert matching a regex blackout on the service field.
        '''
        alert = Alert(
            id='match-service',
            resource='test',
            event='test-event',
            service=['service-blah'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['regex_blackout=2'])

    def test_new_alert_match_tag(self):
        '''
        Test alert matching a regex blackout on the tag(s).
        '''
        alert = Alert(
            id='match-tag',
            resource='test',
            event='test-event',
            service=['test-service'],
            tags=['site=siteX'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['regex_blackout=3'])

    def test_new_alert_no_match_tags(self):
        '''
        Test alert that doesn't match as not all the tags match.
        '''
        alert = Alert(
            id='no-match-tags',
            resource='test',
            event='test-event',
            service=['test-service'],
            tags=['site=siteX', 'role=switch'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.post_receive(alert)
        self.assertEqual(test.status, 'open')
        self.assertEqual(test.tags, [])
