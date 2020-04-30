# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import weakref

from oslo_concurrency import lockutils


_synchronized = lockutils.synchronized_with_prefix("neutron-")


class _CookieMappings(object):
    """A cookie mappings of activated cookies in a Neutron Deployment.

    The cookie is bootstrapped by a Neutron Manager running in
    the context of a Neutron Server process.
    """

    def __init__(self):
        self._cookies = {}

    def add_cookie(self, uuid, cookie):
        """Add or update a cookie of type 'uuid'."""
        self._cookies.update({
            uuid: cookie
        })

    def get_cookie(self, uuid):
        """Get a cookie for a given uuid or None if not present."""
        p = self._cookies.get(uuid)
        return weakref.proxy(p) if p else None

    @property
    def cookies(self):
        """The cookie mappings uuid -> weak reference to the cookie."""
        return dict((x, weakref.proxy(y))
                    for x, y in self._cookies.items())

    @property
    def unique_cookies(self):
        """A sequence of the unique cookies activated in the environments."""
        return tuple(weakref.proxy(x) for x in set(self._cookies.values()))

    @property
    def is_loaded(self):
        """True if the cookies is non empty."""
        return len(self._cookies) > 0


# Create a singleton cookie mappings for send rest request to device.
# Accessing these methods before a Neutron Manager has had the chance
# to load the environment may result in callers handling an empty directory.
_COOKIE_MAPPINGS = None


@_synchronized("cookie_mappings", external=True)
def _create_cookie_mappings():
    global _COOKIE_MAPPINGS
    if _COOKIE_MAPPINGS is None:
        _COOKIE_MAPPINGS = _CookieMappings()
    return _COOKIE_MAPPINGS


def _get_cookie_mappings():
    if _COOKIE_MAPPINGS is None:
        return _create_cookie_mappings()
    return _COOKIE_MAPPINGS


def add_cookie(uuid, cookie):
    _get_cookie_mappings().add_cookie(uuid, cookie)


def get_cookie(uuid):
    return _get_cookie_mappings().get_cookie(uuid)


def get_cookies():
    return _get_cookie_mappings().cookies


def get_unique_cookies():
    return _get_cookie_mappings().unique_cookies


def is_loaded():
    return _get_cookie_mappings().is_loaded
