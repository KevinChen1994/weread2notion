import requests

from .config import WEREAD_API_KEY, WEREAD_API_URL, SKILL_VERSION


class WeReadApi:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {WEREAD_API_KEY}",
            "Content-Type": "application/json",
        })

    def _request(self, api_name, **kwargs):
        body = {"api_name": api_name, "skill_version": SKILL_VERSION, **kwargs}
        resp = self.session.post(WEREAD_API_URL, json=body)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise Exception(f"WeRead API error: {data.get('errmsg', 'unknown')}")
        return data

    def get_shelf(self):
        return self._request("/shelf/sync")

    def get_book_info(self, book_id):
        return self._request("/book/info", bookId=book_id)

    def get_progress(self, book_id):
        return self._request("/book/getprogress", bookId=book_id)

    def get_bookmarks(self, book_id):
        return self._request("/book/bookmarklist", bookId=book_id)

    def get_reviews(self, book_id, synckey=0, count=100):
        return self._request("/review/list/mine", bookid=book_id, synckey=synckey, count=count)

    def get_chapter_info(self, book_id):
        return self._request("/book/chapterinfo", bookId=book_id)

    def get_notebooks(self, count=100, last_sort=None):
        kwargs = {"count": count}
        if last_sort is not None:
            kwargs["lastSort"] = last_sort
        return self._request("/user/notebooks", **kwargs)

    def get_all_notebooks(self):
        """Fetch all notebooks with pagination."""
        books = []
        last_sort = None
        while True:
            data = self.get_notebooks(count=100, last_sort=last_sort)
            page_books = data.get("books", [])
            books.extend(page_books)
            if not data.get("hasMore") or not page_books:
                break
            last_sort = page_books[-1].get("sort")
        return books

    def get_all_reviews(self, book_id):
        """Fetch all reviews for a book with pagination."""
        reviews = []
        synckey = 0
        while True:
            data = self.get_reviews(book_id, synckey=synckey)
            page_reviews = data.get("reviews", [])
            reviews.extend(page_reviews)
            if not data.get("hasMore"):
                break
            synckey = data.get("synckey", 0)
        return reviews

    def get_read_detail(self, mode="overall", base_time=0):
        return self._request("/readdata/detail", mode=mode, baseTime=base_time)
