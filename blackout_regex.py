# -*- coding: utf-8 -*-
'''
Alerta Blackout Regex
=====================

Alerta plugin to enhance the blackout system.
'''
import re
import logging

from alertaclient.api import Client
from alerta.plugins import PluginBase

log = logging.getLogger('alerta.plugins.blackout_regex')

client = Client()


def parse_tags(tag_list):
    return {k: v for k, v in (i.split('=') for i in tag_list if '=' in i)}


class BlackoutRegex(PluginBase):
    def post_receive(self, alert):
        '''
        The regex blackouts are evaluated in the ``post_receive`` in order to
        have the alert already correlated, therefore provide us with the real
        Alert ID (after being correlated, and not just a random fresh ID), the
        tags from the previous evaluation, as well as a pre-filtering by the
        native blackout mechanisms (i.e., if there's a blackout matching the
        alert it won't get to this point - if it gets here we therefore evaluate
        the alert and we're sure it didn't match the literal blackout attributes
        which is ideal to preserve backwards compatibility).
        '''
        blackouts = client.get_blackouts()
        alert_tags = parse_tags(alert.tags)
        log.error(blackouts)

        # When an alert matches a blackout, this plugin adds a special tag
        # ``regex_blackout`` that points to the blackout ID matched.
        # This facilitates the blackout matching, by simply checking if the
        # blackout is still open.
        if 'regex_blackout' in alert_tags:
            log.debug(
                'Checking blackout %s which used to match this alert',
                alert_tags['regex_blackout'],
            )
            for blackout in blackouts:
                if blackout.id == alert_tags['regex_blackout']:
                    log.debug('Found blackout %s', blackout.id)
                    if blackout.status == 'active':
                        log.debug(
                            'Blackout %s is still active, setting alert %s '
                            'status as blackout',
                            blackout.id,
                            alert.id,
                        )
                        alert.set_status('blackout')
                        return alert
            # If the blackout is no longer active, simply return
            # the alert as-is, without changing the status, but
            # removing the regex_blackout tag, so when the alert is
            # fired again, we'll know that it does no longer match
            # an active blackout.
            log.debug(
                'Blackout %s does no longer exist, or is not active, removing '
                'tag and leaving status unchanged',
                alert_tags['regex_blackout'],
            )
            alert.untag(['regex_blackout={}'.format(alert_tags['regex_blackout'])])
            return alert

        # No previous regex blackout match, let's evaluate.
        # The idea is that if a blackout has a number of attributes configured,
        # in order to match, the alert must match all of these attributes.
        for blackout in blackouts:
            # The general assumption is that a blackout has at least one of
            # these attributes set, therefore once we try to match only when an
            # attribute is configured, and skip to the next blackout when the
            # matching fails.
            match = False
            if blackout.group:
                if not re.search(blackout.group, alert.group):
                    log.debug(
                        '%s doesn\'t match the blackout group %s',
                        alert.group,
                        blackout.group,
                    )
                    continue
                match = True
                log.debug('%s matched %s', blackout.group, alert.group)
            if blackout.event:
                if not re.search(blackout.event, alert.event):
                    log.debug(
                        '%s doesn\'t match the blackout event %s',
                        alert.event,
                        blackout.event,
                    )
                    continue
                match = True
                log.debug('%s matched %s', blackout.event, alert.event)
            if blackout.resource:
                if not re.search(blackout.resource, alert.resource):
                    log.debug(
                        '%s doesn\'t match the blackout resource %s',
                        alert.resource,
                        blackout.resource,
                    )
                    continue
                match = True
                log.debug('%s matched %s', blackout.resource, alert.resource)
            if blackout.service:
                if not re.search(blackout.service[0], alert.service[0]):
                    log.debug(
                        '%s doesn\'t match the blackout service %s',
                        alert.service[0],
                        blackout.service[0],
                    )
                    continue
                match = True
                log.debug('%s matched %s', blackout.service[0], alert.service[0])
            if blackout.tags and alert.tags:
                blackout_tags = parse_tags(blackout.tags)
                if not all(
                    [
                        re.search(blackout_tags[blackout_tag], alert_tags[blackout_tag])
                        for blackout_tag in blackout_tags
                        if blackout_tag in alert_tags
                    ]
                ):
                    log.debug(
                        '%s don\'t seem to match the blackout tag(s) %s',
                        str(alert_tags),
                        str(blackout_tags),
                    )
                    continue
                match = True
            if match:
                log.debug(
                    'Alert %s seems to match (regex) blackout %s. '
                    'Adding regex_blackout and status',
                    alert.id,
                    blackout.id,
                )
                alert.tag(['regex_blackout={}'.format(blackout.id)])
                alert.set_status('blackout')
                return alert

        return alert

    def pre_receive(self, alert):
        return alert

    def status_change(self, alert, status, text):
        return alert, status, text
