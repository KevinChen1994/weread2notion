# weread2notion

微信读书同步到 Notion，基于 WeRead Skill API（API Key 鉴权）。

## 关于微信读书 Skills

[微信读书 Skills](https://weread.qq.com/r/weread-skills) 是微信读书官方提供的开放能力平台，允许第三方通过 API Key 方式访问用户的阅读数据，包括书架、阅读进度、划线、笔记、阅读统计等。相比传统的 Cookie 鉴权方式，Skill API Key 更稳定、不会频繁过期，适合用于自动化同步场景。

获取 API Key：访问 https://weread.qq.com/r/weread-skills ，创建 Skill 后即可获得 `wrk-` 开头的 API Key。

## 功能

- 同步书架中所有书籍的元数据到 Notion 数据库（书名、作者、封面、进度、评分等）
- 同步划线和笔记到每本书的页面内，按章节组织
- 增量更新：仅同步有变化的书籍
- 生成阅读时间热力图（类似 GitHub 贡献图）

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入：

```
WEREAD_API_KEY=wrk-xxxxxxxx
NOTION_TOKEN=ntn_xxxxxxxx
NOTION_DATABASE_ID=xxxxxxxx
```

- **WEREAD_API_KEY**：微信读书 Skill API Key
- **NOTION_TOKEN**：Notion Integration Token
- **NOTION_DATABASE_ID**：目标 Notion 数据库 ID

### 3. 运行

```bash
# 同步书籍和笔记
python -m weread2notion

# 强制重写所有笔记
python -m weread2notion --force

# 生成阅读时间热力图
python -m weread2notion --heatmap
```

## Notion 数据库字段

| 字段 | 类型 | 说明 |
|------|------|------|
| 书名 | title | 书名 |
| 作者 | multi_select | 作者列表 |
| 分类 | multi_select | 书籍分类 |
| 封面 | files | 封面图片 |
| ISBN | rich_text | ISBN |
| 简介 | rich_text | 书籍简介 |
| 评分 | number | 微信读书评分 |
| 阅读进度 | number (percent) | 阅读百分比 |
| 阅读时长 | rich_text | 格式：x时x分 |
| 阅读状态 | status | 想读/在读/已读 |
| 阅读天数 | number | 阅读天数 |
| 最后阅读时间 | date | 最后阅读日期 |
| 书架分类 | select | 书架中的分组 |
| 个人评分 | number | 个人评分 |
| 个人评论 | rich_text | 书评内容 |
| 链接 | url | 微信读书链接 |

## GitHub Actions 自动同步

仓库已配置两个定时任务，每天北京时间 8:00 自动执行：

- **Sync WeRead**：同步书籍和笔记到 Notion
- **Sync Heatmap**：生成热力图并提交到仓库

需要在仓库 Settings → Secrets and variables → Actions 中添加：

- `WEREAD_API_KEY`
- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`

## 已知问题

### notion-client 3.x 兼容性

notion-client 3.x SDK 默认使用 `Notion-Version: 2025-09-03` 并将 `databases.query` 迁移到了新的 `data_sources.query` 端点。但目前部分 Notion Integration 尚未支持该新端点，会报 `Could not find database` 错误。

当前的 workaround：手动将 Notion-Version 降为 `2022-06-28`，通过 `client.request()` 调用旧的 `databases/{id}/query` 路径。等 Notion 官方完全迁移后可改回使用 `client.data_sources.query()`。

相关代码：`weread2notion/notion_helper.py` 中的 `NotionHelper.__init__` 和 `get_all_books`。
