class LookupDict(dict):
    """Dictionary lookup object."""

    def __init__(self, name=None):
        self.name = name
        super(LookupDict, self).__init__()

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value


def _build_status_codes():
    """Builds the status code lookup structure."""
    codes = LookupDict(name="status_codes")

    # Mapping of status codes to their primary names and aliases
    status_codes = {
        # Informational
        100: ("continue",),
        101: ("switching_protocols",),
        # Success
        200: ("ok", "okay", "all_ok", "all_good", "\\o/", "✓"),
        201: ("created",),
        202: ("accepted",),
        204: ("no_content",),
        # Redirection
        301: ("moved_permanently", "moved", "resource_moved"),
        302: ("found",),
        304: ("not_modified",),
        # Client Error
        400: ("bad_request", "bad"),
        401: ("unauthorized",),
        403: ("forbidden",),
        404: ("not_found", "404"),
        405: ("method_not_allowed", "not_allowed"),
        # Server Error
        500: ("internal_server_error", "error", "bug"),
        502: ("bad_gateway",),
        503: ("service_unavailable", "unavailable"),
    }

    for code, titles in status_codes.items():
        for title in titles:
            setattr(codes, title, code)
            if not title.startswith("\\"):
                setattr(codes, title.upper(), code)

        # Allow reverse lookup: codes[200] -> 'ok'
        codes[code] = titles[0]

    return codes


codes = _build_status_codes()
