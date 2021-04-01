"""
sanic similarity search server
"""
import logging

from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, json

from es.es_search import get_similar_documents

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Sanic("Wiki Semantic Search")


@app.route("/")
async def root(_: Request) -> HTTPResponse:
    return json({"status": "ok"})


@app.route("/search")
async def search(request: Request) -> HTTPResponse:
    """
    search route
    """
    number_str = request.get_args().get("n", "3")
    if isinstance(number_str, str):
        number = int(number_str)
    else:
        logger.warning("unknown argument 'n' will return 3 candidate pages")
        number = 3
    query = request.json.get("query")
    found_wiki_pages = get_similar_documents(query, number)
    return json(found_wiki_pages)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=1)
