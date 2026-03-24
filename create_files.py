import os

BASE_QUERY = (
    "As a software developer, I want to rewrite the following function/module starting "
    "with the given first iteration of the code and update it based on the following requirements."
)

REQUESTS_PROMPT_ARRAY = [
    (
        "Create error objects from v0 to v1. Define a base exception class and build a hierarchy of specific HTTP error types beneath it.",
        "library-versions/requests/0.2.0/requests-0.2.0/requests/core.py",
    ),
    (
        "Break v0 send() into session methods (v1). Split the single send() method into separate methods for preparation, sending, and redirect handling.",
        "library-versions/requests/0.2.0/requests-0.2.0/requests/core.py",
    ),
    (
        "Recreate Response.__init__ from v0 to v1. Start with a basic response object and add support for raw data, encoding, url, history, cookies and reason.",
        "library-versions/requests/0.2.0/requests-0.2.0/requests/core.py",
    ),
    (
        "Create status codes from v0 to v1. Build a lookup structure that maps numeric HTTP codes to human readable names with multiple aliases.",
        "library-versions/requests/0.2.0/requests-0.2.0/requests/core.py",
    ),
    (
        "CaseInsensitiveDict in structures.py from v1 to v2. Implement a dictionary that treats keys as equal regardless of their casing.",
        "library-versions/requests/1.0.0/requests-1.0.0/requests/structures.py",
    ),
    (
        "cert_verify() in adapters.py from v1 to v2. Refactor SSL certificate verification to support custom CA bundles and client certificates.",
        "library-versions/requests/1.0.0/requests-1.0.0/requests/adapters.py",
    ),
]

PYDANTIC_PROMPT_ARRAY = [
    (
        "Implement BaseModel.dict() from v0 to v1. Start from a basic attribute dump and evolve it to support include, exclude, aliases and nested model serialization.",
        "library-versions/pydantic/0.0.1/pydantic/main.py",
    ),
    (
        "Rewrite conbytes, conlist, constr from v1 to v2. Replace the constraint helper functions with a type annotation approach using explicit constraint classes.",
        "library-versions/pydantic/1.0/pydantic/types.py",
    ),
    (
        "Rewrite PydanticErrorMixin from v1 to v2. Replace implicit error message formatting with explicit error codes and structured message templates.",
        "library-versions/pydantic/1.0/pydantic/errors.py",
    ),
    (
        "Simplify UrlConstraints classes in networks.py (v2). Consolidate the URL type hierarchy into a single configurable class using constraint parameters.",
        "library-versions/pydantic/1.0/pydantic/networks.py",
    ),
    (
        "Validation logic in networks.py. Implement URL and email validation by breaking the process into scheme, host, path and query validation steps,then evolve it to use stricter parsing and error reporting.",
        "library-versions/pydantic/1.0/pydantic/networks.py",
    ),
]


def write_prompts(prefix, prompt_array, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for i, (task, src_path) in enumerate(prompt_array, start=1):
        with open(src_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        content = f"{BASE_QUERY}\n\nRequirement: {task}\n\nSource code:\n\n{source_code}"
        out_path = os.path.join(out_dir, f"{prefix}_{i:02d}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)


write_prompts("requests", REQUESTS_PROMPT_ARRAY, "prompts_")
write_prompts("pydantic", PYDANTIC_PROMPT_ARRAY, "prompts_")
