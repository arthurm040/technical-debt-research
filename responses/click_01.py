import sys

# Mocking _compat for standalone functionality
PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode
else:
    text_type = str


def safecall(func):
    """Wraps a function so that it swallows exceptions (e.g. BrokenPipeError)."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass

    return wrapper


def echo(message=None, file=None, nl=True, err=False):
    """Echoes a message to a file or standard output.

    Evolution:
    v0: Basic print wrapper.
    v1: Added file/stderr toggle (err param).
    v2: Added newline control (nl param).
    v3: Integrated safecall for robust piping.
    v4: Handled NoneType messages as empty strings.
    v5: Implemented complex Python 2/3 encoding logic.
    v6: Added support for binary stream detection.
    v7: Finalized stream type normalization (bytes vs text).
    """
    # Selection of output stream
    if file is None:
        file = sys.stderr if err else sys.stdout

    # v4: Normalize message
    if message is None:
        message = ""

    # v6: Detect if the stream is binary
    # Some streams have a .buffer attribute (Python 3) or 'b' in mode
    is_binary = "b" in getattr(file, "mode", "")
    try:
        if not is_binary and hasattr(file, "buffer"):
            # If we are writing to a text wrapper but want to check if
            # it's possible to write bytes, we check the underlying buffer.
            pass
    except Exception:
        pass

    # Determine newline character based on stream type
    newline = "\n" if not is_binary else b"\n"

    # v5 & v7: Ensure message matches stream type
    if is_binary:
        # If stream is binary, we must provide bytes
        if isinstance(message, text_type):
            encoding = getattr(file, "encoding", None) or "utf-8"
            message = message.encode(encoding, "replace")
    else:
        # If stream is text, we must provide text_type
        if isinstance(message, bytes):
            encoding = getattr(file, "encoding", None) or "utf-8"
            message = message.decode(encoding, "replace")
        elif not isinstance(message, text_type):
            message = text_type(message)

    # v3: Use safecall to prevent crashes on closed pipes
    @safecall
    def _write():
        file.write(message)
        if nl:
            file.write(newline)
        file.flush()

    _write()


# Example Usage:
# echo("Hello World")               # Standard text
# echo("Error occurred", err=True)  # To stderr
# echo("No newline", nl=False)      # No newline
