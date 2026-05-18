# weread2notion

微信读书同步到 Notion，基于 WeRead Skill API（API Key 鉴权）。

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
