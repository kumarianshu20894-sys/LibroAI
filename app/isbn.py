import requests

OPENLIBRARY_URL = "https://openlibrary.org/api/books"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


def _from_openlibrary(isbn):
    resp = requests.get(
        OPENLIBRARY_URL,
        params={"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get(f"ISBN:{isbn}")
    if not data:
        return None

    authors = ", ".join(a.get("name", "") for a in data.get("authors", []) if a.get("name"))
    publishers = data.get("publishers", [])
    publisher = publishers[0].get("name", "") if publishers else ""
    return {
        "title": data.get("title", ""),
        "author": authors,
        "publisher": publisher,
        "description": "",
        "isbn": isbn,
    }


def _from_google_books(isbn):
    resp = requests.get(
        GOOGLE_BOOKS_URL,
        params={"q": f"isbn:{isbn}"},
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return None

    info = items[0].get("volumeInfo", {})
    return {
        "title": info.get("title", ""),
        "author": ", ".join(info.get("authors", [])),
        "publisher": info.get("publisher", ""),
        "description": info.get("description", ""),
        "isbn": isbn,
    }


def fetch_book_by_isbn(isbn):
    """Pehle Open Library, nahi mili to Google Books. Nahi mili to None."""
    isbn = (isbn or "").replace("-", "").strip()
    if not isbn:
        return None

    for source in (_from_openlibrary, _from_google_books):
        try:
            result = source(isbn)
            if result and result.get("title"):
                return result
        except Exception as e:
            # Terminal mein error dikhega, taaki pata chale kya fail hua
            print(f"[ISBN] {source.__name__} failed for {isbn}: {e}")
    return None