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

.. note::

    This shouldn't normally affect the existing blackouts you may have in 
    place, as the regex matching should only kick in *after* the native 
    blackout matching mechanism in Alerta.

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

References
----------

- `Suppressing Alerts using Blackouts 
  <https://docs.alerta.io/en/latest/gettingstarted/tutorial-5-blackouts.html>`_

License
-------

Copyright (c) 2020 Mircea Ulinic. Available under the Apache License 2.0.
