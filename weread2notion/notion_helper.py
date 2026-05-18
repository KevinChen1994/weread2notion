import time

import requests as http_requests
from notion_client import Client

from .config import NOTION_TOKEN, NOTION_DATABASE_ID
from .utils import MAX_LENGTH

NOTION_VERSION = "2022-06-28"


class NotionHelper:
    def __init__(self):
        self.client = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID

    def get_all_books(self):
        """Query all pages in the database, return {bookId: {pageId, sort}}."""
        results = []
        start_cursor = None
        while True:
            kwargs = {"database_id": self.database_id, "page_size": 100}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor
            resp = self.client.databases.query(**kwargs)
            results.extend(resp["results"])
            if not resp.get("has_more"):
                break
            start_cursor = resp.get("next_cursor")

        books = {}
        for page in results:
            props = page["properties"]
            book_id = self._get_rich_text(props.get("BookId"))
            sort_val = self._get_number(props.get("Sort"))
            if book_id:
                books[book_id] = {"pageId": page["id"], "sort": sort_val}
        return books

    def create_book_page(self, properties, icon_url=None):
        kwargs = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        if icon_url:
            kwargs["icon"] = {"type": "external", "external": {"url": icon_url}}
        return self.client.pages.create(**kwargs)

    def update_book_page(self, page_id, properties, icon_url=None):
        kwargs = {"page_id": page_id, "properties": properties}
        if icon_url:
            kwargs["icon"] = {"type": "external", "external": {"url": icon_url}}
        return self.client.pages.update(**kwargs)

    def get_children_blocks(self, page_id):
        blocks = []
        start_cursor = None
        while True:
            kwargs = {"block_id": page_id, "page_size": 100}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor
            resp = self.client.blocks.children.list(**kwargs)
            blocks.extend(resp["results"])
            if not resp.get("has_more"):
                break
            start_cursor = resp.get("next_cursor")
        return blocks

    def clear_page_blocks(self, page_id):
        blocks = self.get_children_blocks(page_id)
        for block in blocks:
            self.client.blocks.delete(block_id=block["id"])

    def append_blocks(self, page_id, blocks):
        return self.client.blocks.children.append(block_id=page_id, children=blocks)

    def append_blocks_after(self, page_id, blocks, after):
        return self.client.blocks.children.append(
            block_id=page_id, children=blocks, after=after
        )

    def upload_file_local(self, file_path, filename=None, content_type=None):
        """Upload a local file to Notion via single_part mode, return file_upload id."""
        import os
        import mimetypes

        if filename is None:
            filename = os.path.basename(file_path)
        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        body = {
            "mode": "single_part",
            "filename": filename,
            "content_type": content_type,
        }
        resp = http_requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers=headers,
            json=body,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        file_id = data.get("id")
        if not file_id:
            return None

        send_headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
        }
        with open(file_path, "rb") as f:
            resp = http_requests.post(
                f"https://api.notion.com/v1/file_uploads/{file_id}/send",
                headers=send_headers,
                files={"file": (filename, f, content_type)},
            )
        if resp.status_code != 200:
            return None
        status = resp.json().get("status")
        if status == "uploaded":
            return file_id
        return None

    def upload_file_from_url(self, url, filename="cover.jpg"):
        """Upload a file to Notion via external_url mode, return file_upload id."""
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        body = {
            "mode": "external_url",
            "external_url": url,
            "filename": filename,
        }
        resp = http_requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers=headers,
            json=body,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        file_id = data.get("id")
        if not file_id:
            return None
        # Wait for import to complete
        for _ in range(20):
            time.sleep(1)
            check = http_requests.get(
                f"https://api.notion.com/v1/file_uploads/{file_id}",
                headers={"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": NOTION_VERSION},
            )
            if check.status_code == 200:
                status = check.json().get("status")
                if status == "uploaded":
                    return file_id
                if status in ("failed", "expired"):
                    return None
        return None

    @staticmethod
    def _get_rich_text(prop):
        if not prop:
            return None
        rt = prop.get("rich_text", [])
        if rt:
            return rt[0].get("plain_text", "")
        return None

    @staticmethod
    def _get_number(prop):
        if not prop:
            return None
        return prop.get("number")

    @staticmethod
    def build_properties(book_data):
        """Build Notion properties dict from book data."""
        props = {}

        if book_data.get("title"):
            props["书名"] = {
                "title": [{"type": "text", "text": {"content": book_data["title"][:MAX_LENGTH]}}]
            }

        if book_data.get("bookId"):
            props["BookId"] = {
                "rich_text": [{"type": "text", "text": {"content": book_data["bookId"]}}]
            }

        if book_data.get("author"):
            authors = [a.strip() for a in book_data["author"].replace(",", " ").replace("，", " ").split() if a.strip()]
            props["作者"] = {"multi_select": [{"name": a} for a in authors]}

        if book_data.get("category"):
            props["分类"] = {"multi_select": [{"name": book_data["category"]}]}

        if book_data.get("cover_file_id"):
            props["封面"] = {
                "files": [{"type": "file_upload", "file_upload": {"id": book_data["cover_file_id"]}, "name": "cover.jpg"}]
            }

        if book_data.get("isbn"):
            props["ISBN"] = {
                "rich_text": [{"type": "text", "text": {"content": book_data["isbn"]}}]
            }

        if book_data.get("intro"):
            props["简介"] = {
                "rich_text": [{"type": "text", "text": {"content": book_data["intro"][:MAX_LENGTH]}}]
            }

        if book_data.get("newRating") is not None:
            rating = book_data["newRating"]
            if isinstance(rating, (int, float)) and rating > 0:
                props["评分"] = {"number": rating / 10}

        if book_data.get("progress") is not None:
            props["阅读进度"] = {"number": book_data["progress"] / 100}

        if book_data.get("readingTime"):
            seconds = book_data["readingTime"]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            time_str = ""
            if hours > 0:
                time_str += f"{hours}时"
            if minutes > 0:
                time_str += f"{minutes}分"
            if not time_str:
                time_str = "0分"
            props["阅读时长"] = {
                "rich_text": [{"type": "text", "text": {"content": time_str}}]
            }

        if book_data.get("readStatus"):
            props["阅读状态"] = {"status": {"name": book_data["readStatus"]}}

        if book_data.get("readDays") is not None:
            props["阅读天数"] = {"number": book_data["readDays"]}

        if book_data.get("lastReadDate"):
            props["最后阅读时间"] = {
                "date": {"start": book_data["lastReadDate"], "time_zone": "Asia/Shanghai"}
            }

        if book_data.get("archive"):
            props["书架分类"] = {"select": {"name": book_data["archive"]}}

        if book_data.get("myRating") is not None:
            props["个人评分"] = {"number": book_data["myRating"]}

        if book_data.get("myReview"):
            props["个人评论"] = {
                "rich_text": [{"type": "text", "text": {"content": book_data["myReview"][:MAX_LENGTH]}}]
            }

        if book_data.get("url"):
            props["链接"] = {"url": book_data["url"]}

        if book_data.get("sort") is not None:
            props["Sort"] = {"number": book_data["sort"]}

        return props
