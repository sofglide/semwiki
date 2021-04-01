"""
Entry point
"""

import click

from wiki import upload_random_pages


@click.group()
def run() -> None:
    pass


run.add_command(upload_random_pages)


if __name__ == "__main__":
    run()
