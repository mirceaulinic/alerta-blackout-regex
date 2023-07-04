# -*- coding: utf-8 -*-
import sys
import logging
import unittest

from mock import MagicMock

app = sys.modules["alerta.app"] = MagicMock()
app.db = MagicMock()

BLACKOUTS = [
    {
        "status": "active",
        "environment": "test",
        "customer": None,
        "tags": [],
        "service": [],
        "resource": r"test\d",
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "1",
    },
    {
        "status": "active",
        "environment": "test",
        "customer": None,
        "tags": [],
        "service": ["service-([a-zA-Z])"],
        "resource": None,
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "2",
    },
    {
        "status": "active",
        "environment": "test",
        "customer": None,
        "tags": ["site=site.*", "role=router"],
        "service": [],
        "resource": None,
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "3",
    },
    {
        "status": "active",
        "environment": "test",
        "customer": None,
        "tags": ["site=site.*", "role=firewall"],
        "service": [],
        "resource": None,
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "4",
    },
    {
        "status": "closed",
        "environment": "test",
        "customer": None,
        "tags": ["site=site.*", "role=router"],
        "service": [],
        "resource": None,
        "event": None,
        "group": None,
        "duration": 3600,
        "endTime": "1985-03-05T22:45:27.425Z",
        "id": "5",
    },
    {
        "status": "closed",
        "environment": r"(rgx|env)",
        "customer": None,
        "tags": [],
        "service": ["test-.*"],
        "resource": "FPC.*",
        "event": "FPCDown",
        "group": None,
        "duration": 3600,
        "endTime": "1985-03-05T22:45:27.425Z",
        "id": "6",
    },
    {
        "status": "active",
        "environment": r"(rgx|env)",
        "customer": None,
        "tags": [],
        "service": [],
        "resource": None,
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "7",
    },
    {
        "status": "active",
        "environment": "customers",
        "customer": "acme",
        "tags": [],
        "service": [],
        "resource": r"test\d",
        "event": None,
        "group": None,
        "duration": 3600,
        "id": "8",
    },
]


class Model:
    def __init__(self, **kwargs):
        for arg, val in kwargs.items():
            setattr(self, arg, val)

    def __str__(self):
        return "{name}({attrs})".format(
            name=self.__class__.__name__,
            attrs=", ".join(
                [
                    "{}={}".format(attr, getattr(self, attr))
                    for attr in dir(self)
                    if not attr.startswith("__")
                ]
            ),
        )


class Blackout(Model):
    pass


class Alert(Model):
    def tag(self, tags):
        self.tags.extend(tags)

    def untag(self, tags):
        for tag in tags:
            if tag in self.tags:
                self.tags.remove(tag)

    def set_status(self, status):
        self.status = status


def _get_blackouts(**kwargs):
    return [Blackout(**blackout) for blackout in BLACKOUTS]


app.db.get_blackouts = _get_blackouts

plugins_mod = sys.modules["alerta.plugins"] = MagicMock()
plugins_mod.PluginBase = MagicMock


from blackout_regex import BlackoutRegex  # pylama: ignore=E402

log = logging.getLogger(__name__)


class TestEnhance(unittest.TestCase):
    def test_new_alert_no_match(self):
        """
        Test alert not matching a regex blackout.
        """
        alert = Alert(
            id="no-match",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=["test-tag"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "open")
        self.assertEqual(test.tags, ["test-tag"])

    def test_new_alert_match_environment(self):
        """
        Test alert matching a regex blackout on the environment field.
        """
        alert = Alert(
            id="match-env",
            environment="rgx",
            customer=None,
            resource="test10",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=[],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["regex_blackout=7"])

    def test_new_alert_match_customer(self):
        """
        Test alert matching a regex blackout on the customer field.
        """
        alert = Alert(
            id="match-customer",
            environment="customers",
            customer="acme",
            resource="test1",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=[],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["regex_blackout=8"])

    def test_new_alert_match_resource(self):
        """
        Test alert matching a regex blackout on the resource field.
        """
        alert = Alert(
            id="match-resource",
            environment="test",
            customer=None,
            resource="test1",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=[],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["regex_blackout=1"])

    def test_new_alert_match_service(self):
        """
        Test alert matching a regex blackout on the service field.
        """
        alert = Alert(
            id="match-service",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["service-blah"],
            tags=[],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["regex_blackout=2"])

    def test_new_alert_match_tag(self):
        """
        Test alert matching a regex blackout on the tag(s).
        """
        alert = Alert(
            id="match-tag",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=["site=siteX", "role=router"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["site=siteX", "role=router", "regex_blackout=3"])

    def test_new_alert_no_match_tags(self):
        """
        Test alert that doesn't match as not all the tags match.
        """
        alert = Alert(
            id="no-match-tags",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=["site=siteX", "role=switch"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "open")
        self.assertEqual(test.tags, ["site=siteX", "role=switch"])

    def test_new_alert_multi_match(self):
        """
        Test alert matching a regex blackout on multiple attributes.
        """
        alert = Alert(
            id="multi-match",
            environment="rgx",
            customer=None,
            resource="FPC1",
            event="FPCDown",
            group="test",
            service=["test-service"],
            tags=["site=siteX"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "blackout")
        self.assertEqual(test.tags, ["site=siteX", "regex_blackout=6"])

    def test_old_alert_inactive_blackout(self):
        """
        Test an existing alert whose associated blackout is currently inactive.
        """
        alert = Alert(
            id="old-alert",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=["site=siteX", "regex_blackout=5"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "open")
        self.assertEqual(test.tags, ["site=siteX"])

    def test_old_alert_removed_blackout(self):
        """
        Test an existing alert whose associated blackout no longer exists.
        """
        alert = Alert(
            id="old-alert",
            environment="test",
            customer=None,
            resource="test::resource",
            event="test-event",
            group="test",
            service=["test-service"],
            tags=["site=siteX", "regex_blackout=99"],
            status="open",
        )
        test_obj = BlackoutRegex()
        test = test_obj.pre_receive(alert)
        self.assertEqual(test.status, "open")
        self.assertEqual(test.tags, ["site=siteX"])
