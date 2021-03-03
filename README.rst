alerta-blackout-regex
=====================

`Alerta <https://alerta.io/>`_ plugin to enhance the blackout management, by 
matching the alerts against blackouts with PCRE (Perl Compatible Regular 
Expression) on attributes.

A blackout is considered matched when all its attributes are matched.

Once an alert is identified as matching a blackout, a special label is applied,
with the format: ``regex_blackout=<blackout id>``, where *blackout id* is the 
ID of the matched blackout, e.g., 
``regex_blackout=d8ba1d3b-dbfd-4677-ab00-e7f8469d7ad3``. This way, when the 
alert is fired again, there's no need to verify the matching again, but simply
verify whether the blackout referenced is still active.

.. versionchanged:: 2.0.0

    Beginning with version 2.0.0, the behaviour has changed, and instead of 
    evaluating the alert into the `post_receive` hook, this plugin now 
    evaluates the alerts through the `pre_receive` hook. The reasoning was that 
    `post_receive` would set the `blackout` status *after* the alert has been 
    sent to other plugins, which has resulted in confusing behaviour.

    That said, the plugin has been changed to process the alert in 
    `pre_receive` and therefore before the alert has been correlated. As the 
    Blackouts are retrieved from the Alerta API as unfortunately there's no 
    other way to gather the Blackouts from a plugin via other internal 
    mechanisms, processing each and every alert throguh `pre_receive` would put 
    a lot more workload on your Alerta API. To reduce this, the 
    `blackout_regex` plugin now caches the Blackouts locally, into a file. To 
    fine tune this behaviour for your own setuo you are able to set a few 
    environment variables. See more details below, under the _Configuration_ 
    section.

Installation
------------

This plugin is designed to be installed on the Alerta server; the package is 
available on PyPI so you can install as:

.. code-block:: bash

    pip install alerta-blackout-regex

Configuration
-------------

Add ``blackout_regex`` to the list of enabled PLUGINS in ``alertad.conf`` server
configuration file and set plugin-specific variables either in the server
configuration file or as environment variables.

.. code-block:: ini

  PLUGINS = ['blackout_regex']

.. note::

    To ensure this plugin won't affect the existing Blackouts you may have in 
    place, it is recommended to list the `blackout_regex` plugin *after* the 
    native `blackout` plugin in the `PLUGINS` configuration option or 
    environment variable.

To model the caching behaviour, from version 2.0.0 onwards, you can set the 
following environment variables:

- `ALERTA_BLACKOUT_CACHE_ENABLED` - boolean value, by default `True`; values that 
  equally provide the `True` logical value: `"True"`, `"true"`, `"1"`, `1`.
- `ALERTA_BLACKOUT_CACHE_FILE` - the location where to cache the blackouts into 
  a file. By default: `/var/cache/alerta/blackout_regex`. Alerta needs writing 
  access to that directory (or at least rights to be able to create the 
  directory), otherwise it'll raise an error; the plugin can go ahead with it, 
  but then it won't be able to cache the Blackouts which may result in an 
  increased workload on your Alerta API.
- `ALERTA_BLACKOUT_CACHE_TIME` - the amount of time to cache the Blackouts for, 
  in seconds. The default value is 60 seconds.

References
----------

- `Suppressing Alerts using Blackouts 
  <https://docs.alerta.io/en/latest/gettingstarted/tutorial-5-blackouts.html>`_

License
-------

Copyright (c) 2020-2021 Mircea Ulinic. Available under the Apache License 2.0.
