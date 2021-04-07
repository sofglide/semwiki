"""
Entry point
"""

import click

from es.es_setup import create_index
from wiki import upload_random_pages


@click.group()
def run() -> None:
    pass


run.add_command(upload_random_pages)
run.add_command(create_index)

if __name__ == "__main__":
    run()
