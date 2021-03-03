# -*- coding: utf-8 -*-
import sys
import logging
import unittest

from mock import MagicMock

client_mod = sys.modules['alertaclient.api'] = MagicMock()
client_mod.Client = MagicMock()

plugins_mod = sys.modules['alerta.plugins'] = MagicMock()
plugins_mod.PluginBase = MagicMock

import blackout_regex
from blackout_regex import BlackoutRegex  # pylama: ignore=E402

blackout_regex.CACHE_ENABLED = False


class Model:
    def __init__(self, **kwargs):
        for arg, val in kwargs.items():
            setattr(self, arg, val)

    def __str__(self):
        return '{name}({attrs})'.format(
            name=self.__class__.__name__,
            attrs=', '.join(
                [
                    '{}={}'.format(attr, getattr(self, attr))
                    for attr in dir(self)
                    if not attr.startswith('__')
                ]
            ),
        )


class Blackout(Model):
    def parse(self, data):
        for field, value in data.items():
            setattr(self, field, data)


class Alert(Model):
    def tag(self, tags):
        self.tags.extend(tags)

    def untag(self, tags):
        for tag in tags:
            if tag in self.tags:
                self.tags.remove(tag)

    def set_status(self, status):
        self.status = status


client_mod.Client.return_value.http.get.return_value = {
    'blackouts': [
        {
            'status': 'active',
            'environment': 'test',
            'tags': [],
            'service': [],
            'resource': r'test\d',
            'event': None,
            'group': None,
            'duration': 3600,
            'id': '1',
        },
        {
            'status': 'active',
            'environment': 'test',
            'tags': [],
            'service': ['service-([a-zA-Z])'],
            'resource': None,
            'event': None,
            'group': None,
            'duration': 3600,
            'id': '2',
        },
        {
            'status': 'active',
            'environment': 'test',
            'tags': ['site=site.*', 'role=router'],
            'service': [],
            'resource': None,
            'event': None,
            'group': None,
            'duration': 3600,
            'id': '3',
        },
        {
            'status': 'active',
            'environment': 'test',
            'tags': ['site=site.*', 'role=firewall'],
            'service': [],
            'resource': None,
            'event': None,
            'group': None,
            'duration': 3600,
            'id': '4',
        },
        {
            'status': 'closed',
            'environment': 'test',
            'tags': ['site=site.*', 'role=router'],
            'service': [],
            'resource': None,
            'event': None,
            'group': None,
            'duration': 3600,
            'endTime': '1985-03-05T22:45:27.425Z',
            'id': '5',
        },
        {
            'status': 'closed',
            'environment': 'test',
            'tags': [],
            'service': [],
            'resource': 'FPC.*',
            'event': 'FPCDown',
            'group': None,
            'duration': 3600,
            'endTime': '1985-03-05T22:45:27.425Z',
            'id': '6',
        },
    ]
}


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
            group='test',
            service=['test-service'],
            tags=[],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
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
            group='test',
            service=['test-service'],
            tags=[],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['regex_blackout=1'])

    def test_new_alert_match_service(self):
        '''
        Test alert matching a regex blackout on the service field.
        '''
        alert = Alert(
            id='match-service',
            resource='test::resource',
            event='test-event',
            group='test',
            service=['service-blah'],
            tags=[],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['regex_blackout=2'])

    def test_new_alert_match_tag(self):
        '''
        Test alert matching a regex blackout on the tag(s).
        '''
        alert = Alert(
            id='match-tag',
            resource='test::resource',
            event='test-event',
            group='test',
            service=['test-service'],
            tags=['site=siteX', 'role=router'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['site=siteX', 'role=router', 'regex_blackout=3'])

    def test_new_alert_no_match_tags(self):
        '''
        Test alert that doesn't match as not all the tags match.
        '''
        alert = Alert(
            id='no-match-tags',
            resource='test::resource',
            event='test-event',
            group='test',
            service=['test-service'],
            tags=['site=siteX', 'role=switch'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'open')
        self.assertEqual(test.tags, ['site=siteX', 'role=switch'])

    def test_new_alert_multi_match(self):
        '''
        Test alert matching a regex blackout on multiple attributes.
        '''
        alert = Alert(
            id='multi-match',
            resource='FPC1',
            event='FPCDown',
            group='test',
            service=['test-service'],
            tags=['site=siteX'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'blackout')
        self.assertEqual(test.tags, ['site=siteX', 'regex_blackout=6'])

    def test_old_alert_inactive_blackout(self):
        '''
        Test an existing alert whose associated blackout is currently inactive.
        '''
        alert = Alert(
            id='old-alert',
            resource='test::resource',
            event='test-event',
            group='test',
            service=['test-service'],
            tags=['site=siteX', 'regex_blackout=5'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'open')
        self.assertEqual(test.tags, ['site=siteX'])

    def test_old_alert_removed_blackout(self):
        '''
        Test an existing alert whose associated blackout no longer exists.
        '''
        alert = Alert(
            id='old-alert',
            resource='test::resource',
            event='test-event',
            group='test',
            service=['test-service'],
            tags=['site=siteX', 'regex_blackout=99'],
            status='open',
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, 'open')
        self.assertEqual(test.tags, ['site=siteX'])
