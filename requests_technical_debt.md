Requests Library - Technical Debt Evolution

v0.2.0

Single file with 400 lines. Wraps urllib2.

Technical debt:
- send() method duplicates 30-40 lines for each HTTP verb
- Direct urllib2 dependency everywhere with no abstraction
- Only catches HTTPError, missing timeout and connection errors
- sent flag requires anyway parameter as workaround
- Uses mutable default arguments
- Only 4 exception types

Summary:
- Code is simple and readable
- API is clean
- Request and Response are separated


v1.0.0

Multiple modules with 2000 lines. Added sessions and adapters.

Fixed from v0.2.0:
- Removed HTTP method duplication by using session.request()
- Added 11 exceptions with proper hierarchy
- Added adapter pattern for transport layer

New technical debt:
- Cookie handling is 300 lines with slow dict operations and complex urllib2 bridging
- Status codes use emoji and ASCII art which can cause encoding issues
- request() calls merge_kwargs() 7 times in a row
- Redirect logic is 80 lines with many edge cases

Summary:
- Sessions persist state
- Adapters are pluggable
- Error handling improved


v2.0.0

Bundled dependencies with 7000+ lines. Uses urllib3 for connection pooling.

Fixed from v1.0.0:
- merge_setting() is cleaner than merge_kwargs()
- PreparedRequest separates user request from wire format
- Connection pooling improves performance

New technical debt:
- Bundles 5000+ lines of urllib3 and charade
- Managing vendored library versions is complex
- Security updates require more work
- Package size increased significantly
- HTTPAdapter is 400 lines with low-level socket code
- Manually implements chunked encoding at socket level instead of using urllib3
- This chunked encoding code is fragile and hard to maintain
- Tightly coupled to urllib3 internals

Summary:
- HTTP/1.1 compliant
- Connection pooling works
- Performance improved


Summary

v0.2.0: 400 lines, 1 module, 4 exceptions. Main issue is code duplication.
v1.0.0: 2000 lines, 10+ modules, 11 exceptions. Main issue is cookie complexity.
v2.0.0: 7000+ lines, 15+ modules, 12 exceptions. Main issue is vendored dependencies.

Each version added features but increased complexity. The library went from simple to feature-rich to performance-focused. Early choices like switching from urllib2 to urllib3 created large changes throughout the codebase.
