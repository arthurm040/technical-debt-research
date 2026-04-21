# -*- coding: utf-8 -*-
"""Field classes for various types of data."""

from __future__ import absolute_import

from marshmallow import class_registry, utils
from marshmallow.base import FieldABC, SchemaABC
from marshmallow.compat import basestring, text_type
from marshmallow.exceptions import (
    MarshallingError,
    UnmarshallingError,
    ValidationError,
)

__all__ = [
    "Field",
    "Raw",
    "Nested",
    "List",
    "String",
    "UUID",
    "Integer",
    "Boolean",
    "Float",
    "DateTime",
    "LocalDateTime",
    "Date",
    "Time",
    "null",
    "missing",
]


class _Null(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        return "<marshmallow.fields.null>"


class _Missing(_Null):
    def __repr__(self):
        return "<marshmallow.fields.missing>"


null = _Null()
missing = _Missing()


class Field(FieldABC):
    """Basic field from which other fields should extend.

    In this version, the Field handles its own serialization and
    deserialization lifecycle.
    """

    _CHECK_ATTRIBUTE = True
    _creation_index = 0

    def __init__(
        self,
        default=null,
        attribute=None,
        validate=None,
        required=False,
        allow_none=None,
        load_from=None,
        dump_to=None,
        **metadata
    ):
        self.default = default
        self.attribute = attribute
        self.required = required
        self.allow_none = allow_none
        self.load_from = load_from
        self.dump_to = dump_to
        self.metadata = metadata

        # Validator setup
        if utils.is_iterable_but_not_string(validate):
            self.validators = list(validate)
        elif callable(validate):
            self.validators = [validate]
        else:
            self.validators = []

        self._creation_index = Field._creation_index
        Field._creation_index += 1
        self.parent = None

    def get_value(self, attr, obj, accessor=None):
        attribute = getattr(self, "attribute", None)
        accessor_func = accessor or utils.get_value
        check_key = attr if attribute is None else attribute
        return accessor_func(check_key, obj)

    def _validate(self, value):
        errors = []
        for validator in self.validators:
            try:
                if validator(value) is False:
                    func_name = utils.get_func_name(validator)
                    errors.append("Validator {0}({1}) is False".format(func_name, value))
            except ValidationError as err:
                errors.extend(err.messages)
        if errors:
            raise ValidationError(errors)

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value and applies formatting."""
        value = self.get_value(attr, obj, accessor=accessor)

        if value is None and self._CHECK_ATTRIBUTE:
            if self.default is not null:
                value = self.default() if callable(self.default) else self.default

        if value is missing or value is null:
            return value

        try:
            return self._serialize(value, attr, obj)
        except Exception as error:
            raise MarshallingError(text_type(error))

    def deserialize(self, value, attr=None, data=None):
        """Validates and restores original data type."""
        if value is missing:
            if self.required:
                raise ValidationError("Missing data for required field.")
            return missing

        if value is None:
            if self.allow_none is False:
                raise ValidationError("Field may not be null.")
            return None

        try:
            output = self._deserialize(value, attr, data)
            self._validate(output)
            return output
        except ValidationError:
            raise
        except Exception as error:
            raise UnmarshallingError(text_type(error))

    # Hooks for concrete classes
    def _serialize(self, value, attr, obj):
        return value

    def _deserialize(self, value, attr, data):
        return value


# --- Concrete Field Implementations ---


class Raw(Field):
    pass


class Nested(Field):
    def __init__(self, nested, default=null, exclude=tuple(), only=None, many=False, **kwargs):
        self.nested = nested
        self.only = only
        self.exclude = exclude
        self.many = many
        self.__schema = None
        super(Nested, self).__init__(default=default, **kwargs)

    @property
    def schema(self):
        if not self.__schema:
            if isinstance(self.nested, SchemaABC):
                self.__schema = self.nested
            elif isinstance(self.nested, type) and issubclass(self.nested, SchemaABC):
                self.__schema = self.nested(many=self.many, only=self.only, exclude=self.exclude)
            elif isinstance(self.nested, basestring):
                schema_class = class_registry.get_class(self.nested)
                self.__schema = schema_class(many=self.many, only=self.only, exclude=self.exclude)
        return self.__schema

    def _serialize(self, nested_obj, attr, obj):
        if nested_obj is None:
            return None
        return self.schema.dump(nested_obj).data

    def _deserialize(self, value, attr, data):
        result, errors = self.schema.load(value)
        if errors:
            raise ValidationError(errors)
        return result


class List(Field):
    def __init__(self, cls_or_instance, **kwargs):
        super(List, self).__init__(**kwargs)
        if isinstance(cls_or_instance, type):
            self.container = cls_or_instance()
        else:
            self.container = cls_or_instance

    def _serialize(self, value, attr, obj):
        if value is None:
            return []
        return [self.container._serialize(each, attr, obj) for each in value]

    def _deserialize(self, value, attr, data):
        if not utils.is_indexable_but_not_string(value):
            raise ValidationError("Not a valid list.")
        return [self.container.deserialize(each) for each in value]


class String(Field):
    def _serialize(self, value, attr, obj):
        return utils.ensure_text_type(value) if value is not None else None

    def _deserialize(self, value, attr, data):
        return utils.ensure_text_type(value)


class Integer(Field):
    def _serialize(self, value, attr, obj):
        return int(value) if value is not None else None

    def _deserialize(self, value, attr, data):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError("Not a valid integer.")


class Boolean(Field):
    falsy = set(["False", "false", "0", "null", "None", "f", "no", "off"])

    def _serialize(self, value, attr, obj):
        return bool(value)

    def _deserialize(self, value, attr, data):
        if text_type(value).lower() in self.falsy:
            return False
        return bool(value)


class DateTime(Field):
    def _serialize(self, value, attr, obj):
        if not value:
            return None
        return value.isoformat()

    def _deserialize(self, value, attr, data):
        try:
            return utils.from_iso(value)
        except (TypeError, ValueError):
            raise ValidationError("Not a valid datetime.")


# Aliases
Str = String
Int = Integer
Bool = Boolean
