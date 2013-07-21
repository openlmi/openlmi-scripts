# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Michal Minar <miminar@redhat.com>
# -*- coding: utf-8 -*-

import abc
import re

import lmi.lmi_client_base
from lmi.scripts.common import get_logger
from lmi.scripts.common import errors
from lmi.scripts.common.command.base import LmiBaseCommand

RE_CALLABLE = re.compile(
        r'^(?P<module>[a-z_]+(?:\.[a-z_]+)*):(?P<func>[a-z_]+)$',
        re.IGNORECASE)
RE_COMMAND_NAME = re.compile('^[a-z]+(-[a-z]+)*$')

LOG = get_logger(__name__)

class EndPointCommandMetaClass(abc.ABCMeta):

    @classmethod
    def _make_execute_method(mcs, bases, dcl, func):
        if func is None:
            for base in bases:
                if hasattr(base, 'execute'):
                    # we already have abstract execute method defined
                    break
            else:
                # prevent instantiation of command without CALLABLE property
                # specified
                dcl['execute'] = abc.abstractmethod(lambda self: None)
        else:
            del dcl['CALLABLE']
            def _execute(_self, *args, **kwargs):
                return func(*args, **kwargs)
            _execute.dest = func
            dcl['execute'] = _execute

    def __new__(mcs, name, bases, dcl):
        try:
            func = dcl.get('CALLABLE')
            if isinstance(func, basestring):
                match = RE_CALLABLE.match(func)
                if not match:
                    raise errors.LmiCommandInvalidCallable(
                            dcl['__module__'], name,
                            'Callable "%s" has invalid format (\':\' expected)'
                            % func)
                mod_name = match.group('module')
                try:
                    func = getattr(__import__(mod_name, globals(), locals(),
                            [match.group('func')], 0),
                            match.group('func'))
                except (ImportError, AttributeError):
                    raise errors.LmiCommandImportFailed(
                            dcl['__module__'], name, func)
        except KeyError:
            mod = dcl['__module__']
            if not name.lower() in mod:
                raise errors.LmiCommandMissingCallable(
                        'Missing CALLABLE attribute for class "%s.%s".' % (
                            mod.__name__, name))
            func = mod[name.lower()]
        if func is not None and not callable(func):
            raise errors.LmiCommandInvalidCallable(
                '"%s" is not a callable object or function.' % (
                    func.__module__ + '.' + func.__name__))

        mcs._make_execute_method(bases, dcl, func)

        return super(EndPointCommandMetaClass, mcs).__new__(
                mcs, name, bases, dcl)

class ListerMetaClass(EndPointCommandMetaClass):

    def __new__(mcs, name, bases, dcl):
        cols = dcl.pop('COLUMNS', None)
        if cols is not None:
            if not isinstance(cols, (list, tuple)):
                raise errors.LmiCommandInvalidProperty(dcl['__module__'], name,
                        'COLUMNS class property must be either list or tuple')
            if not all(isinstance(c, basestring) for c in cols):
                raise errors.LmiCommandInvalidProperty(dcl['__module__'], name,
                        'COLUMNS must contain just column names as strings')
            def _new_get_columns(_cls):
                return cols
            dcl['get_columns'] = classmethod(_new_get_columns)

        return super(ListerMetaClass, mcs).__new__(mcs, name, bases, dcl)

class ShowInstanceMetaClass(EndPointCommandMetaClass):

    @classmethod
    def _check_peroperties(mcs, name, dcl, props):
        if props is not None:
            for prop in props:
                if not isinstance(prop, (basestring, tuple, list)):
                    raise errors.LmiCommandInvalidProperty(
                            dcl['__module__'], name,
                            'PROPERTIES must be a list of strings or tuples')
                if isinstance(prop, (tuple, list)):
                    if (  len(prop) != 2
                       or not isinstance(prop[0], basestring)
                       or not callable(prop[1])):
                        raise errors.LmiCommandInvalidProperty(
                                dcl['__module__'], name,
                            'tuples in PROPERTIES must be: ("name", callable)')

    @classmethod
    def _make_render_all_properties(mcs, bases, dcl):
        for base in bases:
            if hasattr(base, 'render') and not base.render.__isabstractmethod__:
                # we already have abstract execute method defined
                break
        else:
            def _render(_self, inst):
                column_names, values = [], []
                for prop_name, value in inst.properties.items():
                    column_names.append(prop_name)
                    if value is None:
                        value = ''
                    values.append(value)
                return (column_names, values)
            dcl['render'] = _render

    @classmethod
    def _make_render_with_properties(mcs, properties):
        def _render(self, inst):
            column_names, values = [], []
            for prop in properties:
                if isinstance(prop, basestring):
                    prop_name = prop
                    if not prop in inst.properties():
                        LOG().warn('property "%s" not present in instance'
                                ' of "%s"', prop, inst.path)
                        value = "UNKNOWN"
                    else:
                        value = getattr(inst, prop)
                else:
                    prop_name = prop[0]
                    try:
                        value = prop[1](inst)
                    except Exception as exc:
                        if self.app.options.debug:
                            LOG().exception(
                                    'failed to render property "%s"',
                                    prop[0])
                        else:
                            LOG().error(
                                    'failed to render property "%s": %s',
                                    prop[0], exc)
                        value = "ERROR"
                column_names.append(prop_name)
                values.append(value)
            return (column_names, values)
        return _render

    def __new__(mcs, name, bases, dcl):
        dynamic_properties = dcl.pop('DYNAMIC_PROPERTIES', False)
        if dynamic_properties and 'PROPERTIES' in dcl:
            raise errors.LmiCommandError(
                    dcl['__module__'], name,
                    'DYNAMIC_PROPERTIES and PROPERTIES are mutually exclusive')
        properties = dcl.pop('PROPERTIES', None)
        if properties is None and not dynamic_properties:
            mcs._make_render_all_properties(bases, dcl)
        elif properties is None and dynamic_properties:
            def _render_dynamic(self, return_value):
                properties, inst = return_value
                return mcs._make_render_with_properties(properties)(self, inst)
            dcl['render'] = _render_dynamic
        elif properties is not None:
            dcl['render'] = mcs._make_render_with_properties(properties)

        return super(ShowInstanceMetaClass, mcs).__new__(
                mcs, name, bases, dcl)

class CheckResultMetaClass(EndPointCommandMetaClass):

    def __new__(mcs, name, bases, dcl):
        try:
            expect = dcl['EXPECT']
            if callable(expect):
                def _new_expect(self, options, result):
                    if isinstance(result, lmi.lmi_client_base._RValue):
                        result = result.rval
                    passed = expect(options, result)
                    self.result = result
                    return passed
            else:
                def _new_expect(self, _options, result):
                    if isinstance(result, lmi.lmi_client_base._RValue):
                        result = result.rval
                    passed = expect == result
                    self.result = result
                    return passed
                _new_expect.expected = expect
            del dcl['EXPECT']
            dcl['check_result'] = _new_expect
        except KeyError:
            # EXPECT might be defined in some subclass
            pass
            #raise errors.LmiCommandError(dcl['__module__'], name,
                    #'missing EXPECT property')

        return super(CheckResultMetaClass, mcs).__new__(mcs, name, bases, dcl)

class MultiplexerMetaClass(abc.ABCMeta):

    @classmethod
    def _is_root_multiplexer(mcs, bases):
        for base in bases:
            if issubclass(type(base), MultiplexerMetaClass):
                return False
        return True

    def __new__(mcs, name, bases, dcl):
        if not mcs._is_root_multiplexer(bases):
            # check COMMANDS property and make it a classmethod
            if not 'COMMANDS' in dcl:
                raise errors.LmiCommandError('missing COMMANDS property')
            cmds = dcl.pop('COMMANDS')
            if not isinstance(cmds, dict):
                raise errors.LmiCommandInvalidProperty(dcl['__module__'], name,
                        'COMMANDS must be a dictionary')
            if not all(isinstance(c, basestring) for c in cmds.keys()):
                raise errors.LmiCommandInvalidProperty(dcl['__module__'], name,
                        'keys of COMMANDS dictionary must contain command names'
                        ' as strings')
            for cmd_name, cmd in cmds.items():
                if not RE_COMMAND_NAME.match(cmd_name):
                    raise errors.LmiCommandInvalidName(cmd, cmd_name)
                if not issubclass(cmd, LmiBaseCommand):
                    raise errors.LmiCommandError(dcl['__module__'], cmd_name,
                            'COMMANDS dictionary must be composed of'
                            ' LmiCommandBase subclasses, failed class: "%s"'
                            % cmd.__name__)
                if not cmd.is_end_point():
                    cmd.__doc__ = dcl['__doc__']
            def _new_get_commands(_cls):
                return cmds
            dcl['get_commands'] = classmethod(_new_get_commands)

            # check documentation
            if dcl.get('__doc__', None) is None:
                LOG().warn('Command "%s.%s" is missing description string.' % (
                    dcl['__module__'], name))

        return super(MultiplexerMetaClass, mcs).__new__(mcs, name, bases, dcl)
