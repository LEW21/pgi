# Copyright 2012 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

from pgi.glib import gint, gchar_p, gsize, gboolean
from gibaseinfo import GIInfoType
from gifieldinfo import GIFieldInfoPtr
from gicallableinfo import GIFunctionInfoPtr
from giregisteredtypeinfo import GIRegisteredTypeInfo, GIRegisteredTypeInfoPtr
from pgi.ctypesutil import find_library, wrap_class

_gir = find_library("girepository-1.0")


def gi_is_struct_info(base_info, _type=GIInfoType.STRUCT):
    return base_info.get_type().value == _type


class GIStructInfo(GIRegisteredTypeInfo):
    pass


class GIStructInfoPtr(GIRegisteredTypeInfoPtr):
    _type_ = GIStructInfo

    def _get_repr(self):
        values = super(GIStructInfoPtr, self)._get_repr()
        values = {}
        values["size"] = repr(self.get_size())
        values["alignment"] = repr(self.get_alignment())
        values["is_gtype_struct"] = repr(self.is_gtype_struct())
        values["is_foreign"] = repr(self.is_foreign())
        methods = self.get_methods()
        values["methods"] = repr(methods)
        for method in methods:
            method.unref()
        fields = self.get_fields()
        values["fields"] = repr(fields)
        for field in fields:
            field.unref()
        return values

    def get_fields(self):
        return map(self.get_field, xrange(self.get_n_fields()))

    def get_methods(self):
        return map(self.get_method, xrange(self.get_n_methods()))

_methods = [
    ("get_n_fields", gint, [GIStructInfoPtr]),
    ("get_field", GIFieldInfoPtr, [GIStructInfoPtr, gint]),
    ("get_n_methods", gint, [GIStructInfoPtr]),
    ("get_method", GIFunctionInfoPtr, [GIStructInfoPtr, gint]),
    ("find_method", GIFunctionInfoPtr, [GIStructInfoPtr, gchar_p]),
    ("get_size", gsize, [GIStructInfoPtr]),
    ("get_alignment", gsize, [GIStructInfoPtr]),
    ("is_gtype_struct", gboolean, [GIStructInfoPtr]),
    ("is_foreign", gboolean, [GIStructInfoPtr]),
]

wrap_class(_gir, GIStructInfo, GIStructInfoPtr, "g_struct_info_", _methods)

__all__ = ["GIStructInfo", "GIStructInfoPtr", "gi_is_struct_info"]
