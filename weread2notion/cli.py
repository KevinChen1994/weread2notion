import argparse
import sys

from .config import WEREAD_API_KEY, NOTION_TOKEN, NOTION_DATABASE_ID


def main():
    parser = argparse.ArgumentParser(description="微信读书同步到 Notion")
    parser.add_argument("--force", action="store_true", help="强制重写所有笔记（忽略 sort 对比）")
    parser.add_argument("--heatmap", action="store_true", help="同步阅读时间热力图")
    args = parser.parse_args()

    if not WEREAD_API_KEY:
        print("错误: 未设置 WEREAD_API_KEY 环境变量")
        print("请执行: export WEREAD_API_KEY=wrk-xxxxxxxx")
        sys.exit(1)

    if not NOTION_TOKEN:
        print("错误: 未设置 NOTION_TOKEN 环境变量")
        sys.exit(1)

    if not NOTION_DATABASE_ID:
        print("错误: 未设置 NOTION_DATABASE_ID 环境变量")
        sys.exit(1)

    if args.heatmap:
        from .heatmap import sync_heatmap
        sync_heatmap()
    else:
        from .sync import sync_books
        sync_books(force=args.force)


if __name__ == "__main__":
    main()
