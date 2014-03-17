# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.
#
# Authors: Michal Minar <miminar@redhat.com>
#
"""
Package with utilities for checking availability of profiles or CIM classes.
Version requirements can also be specified.
"""

import functools
from pyparsing import ParseException

from lmi.scripts.common import Configuration
from lmi.scripts.common import errors
from lmi.scripts.common.versioncheck import parser

def cmp_profiles(fst, snd):
    """
    Compare two profiles by their version.

    :returns:
        * -1 if the *fst* profile has lower version than *snd*
        * 0  if their versions are equal
        * 1  otherwise
    :rtype: int
    """
    fstver = fst.RegisteredVersion
    sndver = snd.RegisteredVersion
    if fstver == sndver:
        return 0
    return -1 if parser.cmp_version(fstver, sndver) else 1

def get_profile_version(conn, name, cache=None):
    """
    Get version of registered profile on particular broker. Queries
    ``CIM_RegisteredProfile`` and ``CIM_RegisteredSubProfile``. The latter
    comes in question only when ``CIM_RegisteredProfile`` does not yield any
    matching result.

    :param conn: Connection object.
    :param string name: Name of the profile which must match value of *RegisteredName*
        property.
    :param dictionary cache: Optional cache where the result will be stored for
        later use. This greatly speeds up evaluation of several expressions refering
        to same profiles or classes.
    :returns: Version of matching profile found. If there were more of them,
        the highest version will be returned. ``None`` will be returned when no matching
        profile or subprofile is found.
    :rtype: string
    """
    if cache and name in cache:
        return cache[(conn.uri, name)]
    insts = conn.root.interop.wql('SELECT * FROM CIM_RegisteredProfile'
            ' WHERE RegisteredName=\"%s\"' % name)
    regular = set(i for i in insts if i.classname.endswith('RegisteredProfile'))
    if regular:     # select instances of PG_RegisteredProfile if available
        insts = regular
    else:           # otherwise fallback to PG_RegisteredSubProfile instances
        insts = set(i for i in insts if i not in regular)
    if not insts:
        ret = None
    else:
        ret = sorted(insts, cmp=cmp_profiles)[-1].RegisteredVersion
    if cache is not None:
        cache[(conn.uri, name)] = ret
    return ret

def get_class_version(conn, name, namespace=None, cache=None):
    """
    Query broker for version of particular CIM class. Version is stored in
    ``Version`` qualifier of particular CIM class.

    :param conn: Connection object.
    :param string name: Name of class to query.
    :param string namespace: Optional CIM namespace. Defaults to configured namespace.
    :param dictionary cache: Optional cache used to speed up expression prrocessing.
    :returns: Version of CIM matching class. Empty string if class is registered but
        is missing ``Version`` qualifier and ``None`` if it is not registered.
    :rtype: string
    """
    if namespace is None:
        namespace = Configuration.get_instance().namespace
    if cache and (namespace, name) in cache:
        return cache[(conn.uri, namespace, name)]
    ns = conn.get_namespace(namespace)
    cls = getattr(ns, name, None)
    if not cls:
        ret = None
    else:
        quals = cls.wrapped_object.qualifiers
        if 'Version' not in quals:
            ret = ''
        else:
            ret = quals['Version'].value
    if cache is not None:
        cache[(conn.uri, namespace, name)] = ret
    return ret

def eval_respl(expr, conn, namespace=None, cache=None):
    """
    Evaluate LMIReSpL expression on particular broker.

    :param string expr: Expression to evaluate.
    :param conn: Connection object.
    :param string namespace: Optional CIM namespace where CIM classes will be
        searched.
    :param dictionary cache: Optional cache speeding up evaluation.
    :returns: ``True`` if requirements in expression are satisfied.
    :rtype: boolean
    """
    if namespace is None:
        namespace = Configuration.get_instance().namespace
    stack = []
    pvget = functools.partial(get_profile_version, conn, cache=cache)
    cvget = functools.partial(get_class_version, conn,
            namespace=namespace, cache=cache)
    pr = parser.bnf_parser(stack, pvget, cvget)
    pr.parseString(expr, parseAll=True)
    # Now evaluate starting non-terminal created on stack.
    return stack[0]()

