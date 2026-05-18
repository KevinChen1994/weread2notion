import time

from .weread_api import WeReadApi
from .notion_helper import NotionHelper
from .utils import (
    build_table_of_contents,
    build_heading,
    build_callout,
    build_quote,
    timestamp_to_date,
)


def sync_books(force=False):
    weread = WeReadApi()
    notion = NotionHelper()

    print("正在获取书架...")
    shelf_data = weread.get_shelf()
    shelf_books = shelf_data.get("books", [])
    archives = shelf_data.get("archive", [])

    archive_map = {}
    for arch in archives:
        for bid in arch.get("bookIds", []):
            archive_map[bid] = arch.get("name", "")

    print("正在获取笔记本列表...")
    notebooks = weread.get_all_notebooks()
    notebook_map = {nb.get("bookId"): nb.get("sort", 0) for nb in notebooks}

    print("正在获取 Notion 数据库...")
    notion_books = notion.get_all_books()

    print(f"书架共 {len(shelf_books)} 本书，Notion 已有 {len(notion_books)} 本")

    for idx, book in enumerate(shelf_books):
        book_id = book.get("bookId")
        title = book.get("title", "")
        read_update_time = book.get("readUpdateTime", 0)

        if book_id in notion_books and not force:
            existing_sort = notion_books[book_id].get("sort") or 0
            if existing_sort == read_update_time:
                continue

        print(f"[{idx+1}/{len(shelf_books)}] 正在同步《{title}》...")

        book_data = _build_book_data(weread, book, archive_map, read_update_time)

        if book_data.get("cover"):
            file_id = notion.upload_file_from_url(book_data["cover"])
            if file_id:
                book_data["cover_file_id"] = file_id

        if book_id in notion_books:
            page_id = notion_books[book_id]["pageId"]
            properties = NotionHelper.build_properties(book_data)
            notion.update_book_page(page_id, properties, icon_url=book_data.get("cover"))
        else:
            properties = NotionHelper.build_properties(book_data)
            result = notion.create_book_page(properties, icon_url=book_data.get("cover"))
            notion_books[book_id] = {"pageId": result["id"], "sort": read_update_time}

        time.sleep(0.3)

    print("\n书籍元数据同步完成，开始同步笔记...")
    sync_notes(weread, notion, notion_books, notebook_map, force)
    print("\n同步完成！")


def _build_book_data(weread, book, archive_map, read_update_time):
    book_id = book.get("bookId")
    data = {
        "title": book.get("title", ""),
        "bookId": book_id,
        "author": book.get("author", ""),
        "category": book.get("category", ""),
        "cover": book.get("cover", ""),
        "sort": read_update_time,
        "url": f"https://weread.qq.com/web/reader/{book_id}",
    }

    if archive_map.get(book_id):
        data["archive"] = archive_map[book_id]

    if read_update_time:
        data["lastReadDate"] = timestamp_to_date(read_update_time)

    try:
        info = weread.get_book_info(book_id)
        data["isbn"] = info.get("isbn", "")
        data["intro"] = info.get("intro", "")
        data["newRating"] = info.get("newRating", 0)
    except Exception:
        pass

    try:
        progress_data = weread.get_progress(book_id)
        book_progress = progress_data.get("book", {})
        data["progress"] = book_progress.get("progress", 0)
        data["readingTime"] = book_progress.get("recordReadingTime") or book_progress.get("readingTime") or progress_data.get("recordReadingTime") or progress_data.get("readingTime") or 0
        if data["readingTime"] == 0 and book_id == (shelf_books[0].get("bookId") if 'shelf_books' in dir() else ""):
            print(f"    [DEBUG] progress response keys: {list(progress_data.keys())}")
            print(f"    [DEBUG] book keys: {list(book_progress.keys())}")
        finish_reading = 1 if book_progress.get("progress") == 100 else 0

        if finish_reading:
            data["readStatus"] = "已读"
        elif book_progress.get("progress", 0) > 0:
            data["readStatus"] = "在读"
        else:
            data["readStatus"] = "想读"
    except Exception:
        data["readStatus"] = "想读"

    try:
        reviews = weread.get_all_reviews(book_id)
        for r in reviews:
            review = r.get("review", {})
            if review.get("type") == 4:
                star = review.get("star", 0)
                if star > 0:
                    data["myRating"] = star
                content = review.get("content", "")
                if content:
                    data["myReview"] = content
                break
    except Exception:
        pass

    return data


def sync_notes(weread, notion, notion_books, notebook_map, force=False):
    books_to_sync = []
    for book_id, nb_sort in notebook_map.items():
        if book_id not in notion_books:
            continue
        existing_sort = notion_books[book_id].get("sort") or 0
        if not force and existing_sort == nb_sort:
            continue
        books_to_sync.append((book_id, nb_sort))

    if not books_to_sync:
        print("没有需要同步笔记的书籍")
        return

    print(f"共 {len(books_to_sync)} 本书需要同步笔记")

    for idx, (book_id, nb_sort) in enumerate(books_to_sync):
        page_id = notion_books[book_id]["pageId"]
        print(f"  [{idx+1}/{len(books_to_sync)}] 正在同步笔记...")

        try:
            bookmarks_data = weread.get_bookmarks(book_id)
            bookmarks = bookmarks_data.get("updated", [])
            chapters_from_bm = {
                c["chapterUid"]: c["title"]
                for c in bookmarks_data.get("chapters", [])
            }

            reviews = weread.get_all_reviews(book_id)
            review_list = []
            for r in reviews:
                review = r.get("review", {})
                if review.get("type") == 4:
                    continue
                review_list.append(review)

            chapter_info = {}
            try:
                ch_data = weread.get_chapter_info(book_id)
                for ch in ch_data.get("chapters", []):
                    chapter_info[ch["chapterUid"]] = {
                        "title": ch["title"],
                        "level": ch.get("level", 1),
                    }
            except Exception:
                pass

            for uid, title in chapters_from_bm.items():
                if uid not in chapter_info:
                    chapter_info[uid] = {"title": title, "level": 2}

            blocks = _build_note_blocks(bookmarks, review_list, chapter_info)

            notion.clear_page_blocks(page_id)
            _batch_append_blocks(notion, page_id, blocks)

            notion.update_book_page(page_id, {"Sort": {"number": nb_sort}})

        except Exception as e:
            print(f"    同步失败: {e}")

        time.sleep(0.5)


def _build_note_blocks(bookmarks, reviews, chapter_info):
    items = []

    for bm in bookmarks:
        items.append({
            "type": "bookmark",
            "chapterUid": bm.get("chapterUid", 0),
            "range": bm.get("range", ""),
            "markText": bm.get("markText", ""),
            "style": bm.get("style", 0),
            "colorStyle": bm.get("colorStyle", 0),
        })

    for rv in reviews:
        chapterUid = rv.get("chapterUid", 0)
        items.append({
            "type": "review",
            "chapterUid": chapterUid,
            "range": rv.get("range", ""),
            "content": rv.get("content", ""),
            "abstract": rv.get("abstract", ""),
            "style": rv.get("style", 0),
            "colorStyle": rv.get("colorStyle", 0),
        })

    items.sort(key=lambda x: (
        x.get("chapterUid", 0),
        int(x["range"].split("-")[0]) if x.get("range") and x["range"].split("-")[0].isdigit() else 0,
    ))

    blocks = [build_table_of_contents()]
    current_chapter = None

    for item in items:
        chapter_uid = item.get("chapterUid", 0)
        if chapter_uid != current_chapter and chapter_uid in chapter_info:
            current_chapter = chapter_uid
            ch = chapter_info[chapter_uid]
            blocks.append(build_heading(ch.get("level", 2), ch["title"]))

        if item["type"] == "bookmark":
            blocks.append(build_callout(
                item["markText"],
                style=item.get("style", 0),
                color_style=item.get("colorStyle", 0),
            ))
        elif item["type"] == "review":
            block = build_callout(
                item["content"],
                is_review=True,
            )
            if item.get("abstract"):
                block["callout"]["children"] = [build_quote(item["abstract"])]
            blocks.append(block)

    return blocks


def _batch_append_blocks(notion, page_id, blocks):
    BATCH_SIZE = 100
    for i in range(0, len(blocks), BATCH_SIZE):
        batch = blocks[i:i + BATCH_SIZE]
        notion.append_blocks(page_id, batch)
        if i + BATCH_SIZE < len(blocks):
            time.sleep(0.3)
