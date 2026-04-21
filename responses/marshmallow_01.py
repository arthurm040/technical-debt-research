# -*- coding: utf-8 -*-
"""Exception classes for marshmallow-related errors."""


class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""

    pass


class _WrappingException(MarshmallowError):
    """Exception that wraps a different, underlying exception. Used so that
    an error in serialization or deserialization can be reraised as a
    :exc:`MarshmallowError <MarshmallowError>`.
    """

    def __init__(self, underlying_exception):
        if isinstance(underlying_exception, Exception):
            self.underlying_exception = underlying_exception
        else:
            self.underlying_exception = None
        super().__init__(str(underlying_exception))


class ForcedError(_WrappingException):
    """Error that always gets raised, even during serialization.
    Field classes should raise this error if the error should not be stored in
    the Marshaller's error dictionary and should instead be raised.
    """

    pass


class ValidationError(MarshmallowError):
    """Raised when validation fails on a field or schema.

    :param message: An error message, list of error messages, or dict of
        error messages.
    :param str field_name: Name of the field to store the error on. If None,
        the error is stored in its default location ("_schema").
    :param data: The raw input data that failed validation.
    :param valid_data: The partially validated data.
    """

    def __init__(self, message, field_name=None, data=None, valid_data=None, **kwargs):
        self.messages = [message] if isinstance(message, (str, bytes)) else message
        self.field_name = field_name
        self.data = data
        self.valid_data = valid_data
        self.kwargs = kwargs
        super().__init__(self.messages)

    def normalized_messages(self):
        """Standardizes messages into a dict of lists.
        If the input was a dictionary, it returns it. Otherwise, it wraps the
        list of messages in a dictionary keyed by the field name.
        """
        if isinstance(self.messages, dict):
            return self.messages

        # Determine the key: use field_name if provided, otherwise default to _schema
        key = self.field_name or "_schema"

        # Ensure the value is a list
        value = self.messages if isinstance(self.messages, list) else [self.messages]
        return {key: value}

    @property
    def messages_dict(self):
        """A structured dictionary containing field-level error grouping."""
        return self.normalized_messages()


class RegistryError(ForcedError, NameError):
    """Raised when an invalid operation is performed on the serializer
    class registry.
    """

    pass


class MarshallingError(_WrappingException):
    """Raised in case of a marshalling error. If raised during serialization,
    the error is caught and the error message is stored in an ``errors``
    dictionary.
    """

    pass


class UnmarshallingError(_WrappingException):
    """Raised when invalid data are passed to a deserialization function. If
    raised during deserialization, the error is caught and the error message
    is stored in an ``errors`` dictionary.
    """

    pass
