from ._compat import PY2, filename_to_ui, get_text_stderr
from .utils import echo


class ClickException(Exception):
    """An exception that click can handle and show to the user."""

    exit_code = 1

    def __init__(self, message):
        if PY2:
            Exception.__init__(self, message.encode("utf-8"))
        else:
            Exception.__init__(self, message)
        self.message = message

    def format_message(self):
        return self.message

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        echo("Error: %s" % self.format_message(), file=file)


class UsageError(ClickException):
    """An internal exception that signals a usage error."""

    exit_code = 2

    def __init__(self, message, ctx=None):
        ClickException.__init__(self, message)
        self.ctx = ctx

    def show(self, file=None):
        if file is None:
            file = get_text_stderr()
        if self.ctx is not None:
            echo(self.ctx.get_usage() + "\n", file=file)
        echo("Error: %s" % self.format_message(), file=file)


class BadParameter(UsageError):
    """An exception that formats out a standardized error message for a
    bad parameter.
    """

    def __init__(self, message, ctx=None, param=None, param_hint=None):
        UsageError.__init__(self, message, ctx)
        self.param = param
        self.param_hint = param_hint

    def format_message(self):
        if self.param_hint is not None:
            param_hint = self.param_hint
        elif self.param is not None:
            param_hint = self.param.opts or [self.param.name]
        else:
            return "Invalid value: %s" % self.message

        if isinstance(param_hint, (tuple, list)):
            param_hint = " / ".join('"%s"' % x for x in param_hint)
        return "Invalid value for %s: %s" % (param_hint, self.message)


class MissingParameter(BadParameter):
    """Raised if parameter is missing but required.

    .. versionadded:: 4.0
    """

    def __init__(self, message=None, ctx=None, param=None, param_hint=None):
        UsageError.__init__(self, message, ctx)
        self.param = param
        self.param_hint = param_hint

    def format_message(self):
        if self.param_hint is not None:
            param_hint = self.param_hint
        elif self.param is not None:
            param_hint = self.param.opts or [self.param.name]
        else:
            param_hint = None

        if isinstance(param_hint, (tuple, list)):
            param_hint = " / ".join('"%s"' % x for x in param_hint)

        msg = self.message or "Missing parameter"
        if param_hint:
            return "%s: %s" % (msg, param_hint)
        return msg


class NoSuchOption(UsageError):
    """Raised if click attempted to handle an option that does not exist.

    .. versionadded:: 4.0
    """

    def __init__(self, option_name, message=None, possibilities=None, ctx=None):
        if message is None:
            message = "no such option: %s" % option_name
        UsageError.__init__(self, message, ctx)
        self.option_name = option_name
        self.possibilities = possibilities

    def format_message(self):
        bits = [self.message]
        if self.possibilities:
            if len(self.possibilities) == 1:
                bits.append("Did you mean %s?" % self.possibilities[0])
            else:
                bits.append("(Possible options: %s)" % ", ".join(self.possibilities))
        return " ".join(bits)


class BadOptionUsage(UsageError):
    """Raised if an option is generally misused.

    .. versionadded:: 4.0
    """

    def __init__(self, option_name, message, ctx=None):
        UsageError.__init__(self, message, ctx)
        self.option_name = option_name


class BadArgumentUsage(UsageError):
    """Raised if an argument is generally misused.

    .. versionadded:: 4.0
    """

    def __init__(self, message, ctx=None):
        UsageError.__init__(self, message, ctx)


class FileError(ClickException):
    """Raised if a file cannot be opened."""

    def __init__(self, filename, hint=None):
        ui_filename = filename_to_ui(filename)
        if hint is None:
            hint = "unknown error"
        ClickException.__init__(self, hint)
        self.ui_filename = ui_filename
        self.filename = filename

    def format_message(self):
        return "Could not open file %s: %s" % (self.ui_filename, self.message)


class Abort(RuntimeError):
    """An internal signalling exception that signals click to abort."""
