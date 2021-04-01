"""
creating wikipedia pages in s3 bucket
"""
import json
import logging
from typing import Dict

import boto3
import click
import wikipedia
from smart_open import open as smart_open

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
s3 = boto3.resource("s3")


def get_random_page() -> Dict[str, str]:
    """
    fetches a random page from wikipedia and returns a dict of page attributes
    """
    while True:
        try:
            title = wikipedia.random()
            wiki_page = wikipedia.page(title)
            break
        except wikipedia.WikipediaException:
            pass

    page = {
        "title": wiki_page.title,
        "content": wiki_page.content,
        "pageid": int(wiki_page.pageid),
        "url": wiki_page.url,
    }
    return page


@click.command(help="upload random pages to S3 bucket")
@click.option("--number", "-n", type=click.INT, default=1, help="number of random pages to upload")
def upload_random_pages(number: int = 1) -> None:
    """
    uploads a number of random pages from wikipedia to s3
    """
    s3_bucket = config.get_s3_bucket()
    s3_prefix = config.get_s3_prefix()
    for count in range(number):
        page = get_random_page()
        s3_file_key = f"S3://{s3_bucket}/{s3_prefix}/{page['pageid']}"
        with smart_open(s3_file_key, "w") as fp:
            json.dump(page, fp)
        logger.info(f"uploaded page {count + 1}/{number}")


if __name__ == "__main__":
    # random_page = get_random_page()

    upload_random_pages()
