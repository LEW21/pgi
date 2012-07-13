# Copyright (C) 2010 Ignacio Casal Quinteiro <icq@gnome.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

import sys

from _override import override
from pgi import Gio

__all__ = []


class FileEnumerator(Gio.FileEnumerator):
    def __iter__(self):
        return self

    def __next__(self):
        file_info = self.next_file(None)

        if file_info is not None:
            return file_info
        else:
            raise StopIteration

    # python 2 compat for the iter protocol
    next = __next__


FileEnumerator = override(FileEnumerator)
__all__.append('FileEnumerator')


class Settings(Gio.Settings):
    '''Provide dictionary-like access to GLib.Settings.'''

    def __init__(self, schema, path=None, backend=None, **kwargs):
        Gio.Settings.__init__(self, schema=schema, backend=backend, path=path, **kwargs)

    def __contains__(self, key):
        return key in self.list_keys()

    def __len__(self):
        return len(self.list_keys())

    def __bool__(self):
        # for "if mysettings" we don't want a dictionary-like test here, just
        # if the object isn't None
        return True

    # alias for Python 2.x object protocol
    __nonzero__ = __bool__

    def __getitem__(self, key):
        # get_value() aborts the program on an unknown key
        if not key in self:
            raise KeyError('unknown key: %r' % (key,))

        return self.get_value(key).unpack()

    def __setitem__(self, key, value):
        # set_value() aborts the program on an unknown key
        if not key in self:
            raise KeyError('unknown key: %r' % (key,))

        # determine type string of this key
        range = self.get_range(key)
        type_ = range.get_child_value(0).get_string()
        v = range.get_child_value(1)
        if type_ == 'type':
            # v is boxed empty array, type of its elements is the allowed value type
            type_str = v.get_child_value(0).get_type_string()
            assert type_str.startswith('a')
            type_str = type_str[1:]
        else:
            raise NotImplementedError('Cannot handle allowed type range class' + str(type_))

        self.set_value(key, GLib.Variant(type_str, value))

    def keys(self):
        return self.list_keys()

Settings = override(Settings)
__all__.append('Settings')


class _DBusProxyMethodCall:
    '''Helper class to implement DBusProxy method calls.'''

    def __init__(self, dbus_proxy, method_name):
        self.dbus_proxy = dbus_proxy
        self.method_name = method_name

    def __async_result_handler(self, obj, result, user_data):
        (result_callback, error_callback, real_user_data) = user_data
        try:
            ret = obj.call_finish(result)
        except Exception:
            etype, e = sys.exc_info()[:2]
            # return exception as value
            if error_callback:
                error_callback(obj, e, real_user_data)
            else:
                result_callback(obj, e, real_user_data)
            return

        result_callback(obj, self._unpack_result(ret), real_user_data)

    def __call__(self, *args, **kwargs):
        # the first positional argument is the signature, unless we are calling
        # a method without arguments; then signature is implied to be '()'.
        if args:
            signature = args[0]
            args = args[1:]
            if not isinstance(signature, str):
                raise TypeError('first argument must be the method signature string: %r' % signature)
        else:
            signature = '()'

        arg_variant = GLib.Variant(signature, tuple(args))

        if 'result_handler' in kwargs:
            # asynchronous call
            user_data = (kwargs['result_handler'],
                    kwargs.get('error_handler'), kwargs.get('user_data'))
            self.dbus_proxy.call(self.method_name, arg_variant,
                    kwargs.get('flags', 0), kwargs.get('timeout', -1), None,
                    self.__async_result_handler, user_data)
        else:
            # synchronous call
            result = self.dbus_proxy.call_sync(self.method_name, arg_variant,
                    kwargs.get('flags', 0), kwargs.get('timeout', -1), None)
            return self._unpack_result(result)

    @classmethod
    def _unpack_result(klass, result):
        '''Convert a D-BUS return variant into an appropriate return value'''

        result = result.unpack()

        # to be compatible with standard Python behaviour, unbox
        # single-element tuples and return None for empty result tuples
        if len(result) == 1:
            result = result[0]
        elif len(result) == 0:
            result = None

        return result


class DBusProxy(Gio.DBusProxy):
    '''Provide comfortable and pythonic method calls.

    This marshalls the method arguments into a GVariant, invokes the
    call_sync() method on the DBusProxy object, and unmarshalls the result
    GVariant back into a Python tuple.

    The first argument always needs to be the D-Bus signature tuple of the
    method call. Example:

      proxy = Gio.DBusProxy.new_sync(...)
      result = proxy.MyMethod('(is)', 42, 'hello')

    The exception are methods which take no arguments, like
    proxy.MyMethod('()'). For these you can omit the signature and just write
    proxy.MyMethod().

    Optional keyword arguments:

    - timeout: timeout for the call in milliseconds (default to D-Bus timeout)

    - flags: Combination of Gio.DBusCallFlags.*

    - result_handler: Do an asynchronous method call and invoke
         result_handler(proxy_object, result, user_data) when it finishes.

    - error_handler: If the asynchronous call raises an exception,
      error_handler(proxy_object, exception, user_data) is called when it
      finishes. If error_handler is not given, result_handler is called with
      the exception object as result instead.

    - user_data: Optional user data to pass to result_handler for
      asynchronous calls.

    Example for asynchronous calls:

      def mymethod_done(proxy, result, user_data):
          if isinstance(result, Exception):
              # handle error
          else:
              # do something with result

      proxy.MyMethod('(is)', 42, 'hello',
          result_handler=mymethod_done, user_data='data')
    '''
    def __getattr__(self, name):
        return _DBusProxyMethodCall(self, name)

DBusProxy = override(DBusProxy)
__all__.append('DBusProxy')
