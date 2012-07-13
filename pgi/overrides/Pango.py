# Copyright (C) 2010 Paolo Borelli <pborelli@gnome.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from pgi import Pango
from _override import override


__all__ = []


class Context(Pango.Context):

    def get_metrics(self, desc, language=None):
        return super(Context, self).get_metrics(desc, language)

Context = override(Context)
__all__.append('Context')


class FontDescription(Pango.FontDescription):

    def __new__(cls, string=None):
        if string is not None:
            return Pango.font_description_from_string(string)
        else:
            return Pango.FontDescription.__new__(cls)

FontDescription = override(FontDescription)
__all__.append('FontDescription')


class Layout(Pango.Layout):

    def __new__(cls, context):
        return Pango.Layout.new(context)

    def __init__(self, context, **kwds):
        # simply discard 'context', since it was set by
        # __new__ and it is not a PangoLayout property
        super(Layout, self).__init__(**kwds)

    def set_markup(self, text, length=-1):
        super(Layout, self).set_markup(text, length)

Layout = override(Layout)
__all__.append('Layout')
