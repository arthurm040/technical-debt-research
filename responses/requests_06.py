def cert_verify(self, conn, url, verify, cert):
    """Verify a certificate for a given connection."""
    if url.lower().startswith("https"):
        cert_loc = None

        # 1. Handle CA Bundle Verification
        if verify:
            # If verify is a path to a CA bundle
            if verify is not True:
                cert_loc = verify

            # Look for configuration in environment if trust_env is enabled
            if not cert_loc and self.config.get("trust_env"):
                cert_loc = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("CURL_CA_BUNDLE")

            # Fallback to default bundle
            if not cert_loc:
                cert_loc = DEFAULT_CA_BUNDLE_PATH

            if not cert_loc or not os.path.exists(cert_loc):
                raise IOError(
                    "Could not find a suitable TLS CA certificate bundle, " "invalid path: {}".format(cert_loc)
                )

            conn.cert_reqs = "CERT_REQUIRED"
            conn.ca_certs = cert_loc
        else:
            conn.cert_reqs = "CERT_NONE"
            conn.ca_certs = None

        # 2. Handle Client Certificates
        if cert:
            if isinstance(cert, tuple) and len(cert) == 2:
                conn.cert_file = cert[0]
                conn.key_file = cert[1]
            else:
                conn.cert_file = cert
                conn.key_file = None

    # Non-HTTPS connections don't need cert logic
