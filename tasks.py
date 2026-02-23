from invoke import task


@task
def lint(c):
    c.run("""
    set -e
    black -l 120 --preview .
    ruff check --select "B,D,E,F,I" --ignore D103,D100 --line-length 120 --fix --show-fixes .
    """)
