# GitHub AI 技术热点日报与趋势周报

这是一个完全运行在 GitHub Actions 上的自动化项目，用于收集 GitHub 上 AI 相关热门技术项目，并生成中文日报和周报。项目不依赖本地电脑，不接入 OpenAI API 或其他外部大模型，所有内容基于 GitHub Search API 数据和本地规则生成。

## 自动化运行方式

- 每天北京时间 08:00 生成日报：`reports/daily/YYYY-MM-DD.md`
- 每周一北京时间 08:30 生成周报：`reports/weekly/YYYY-WW.md`
- 每次日报同时保存 JSON 缓存：`reports/daily/YYYY-MM-DD.json`
- workflow 会自动提交 `reports/` 下的新报告

GitHub Actions 的 cron 使用 UTC 时间，所以：

- 北京时间每天 08:00 = UTC `0 0 * * *`
- 北京时间周一 08:30 = UTC `30 0 * * 1`

## 手动运行 Workflow

在 GitHub 仓库页面进入 `Actions`，选择 `AI Trends Reports`，点击 `Run workflow`，然后选择：

- `daily`：只生成日报
- `weekly`：只生成周报
- `both`：同时生成日报和周报

## 本地调试

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --mode daily --days 7 --limit 50 --min-stars 50
python run.py --mode weekly --days 7 --limit 100 --min-stars 50
```

如需更高 API 限额，可设置：

```bash
export GITHUB_TOKEN=你的 GitHub token
```

代码不会写死 token，只会从环境变量 `GITHUB_TOKEN` 读取。GitHub Actions 中默认使用 `${{ secrets.GITHUB_TOKEN }}`。

## 如何修改关键词

关键词集中维护在 `config/keywords.yml`。你可以按技术方向新增分类，也可以在已有分类中加入关键词。采集器会用每个关键词调用 GitHub Search API，并记录命中的 `matched_keywords`，日报和周报会据此统计关键词趋势。

## 如何调整评分规则

评分逻辑位于 `src/scorer.py`：

```text
trend_score =
  stars_score * 0.35
  + forks_score * 0.15
  + recency_score * 0.20
  + keyword_score * 0.20
  + topic_score * 0.10
```

- `stars_score` 和 `forks_score` 使用 log 归一化，避免超大项目完全碾压新项目
- `recency_score` 根据 `pushed_at` 计算，越近期更新得分越高
- `keyword_score` 根据 name、topics、description 的命中情况计算
- `topic_score` 对 AI 相关 GitHub topics 加权

## 报告内容

日报包括：

- 今日概览
- 今日 Top 项目
- 技术方向分布
- 关键词命中统计
- 值得持续跟踪项目

周报包括：

- 本周总结
- 本周 Top 20 项目
- 按技术方向归类
- 本周关键词趋势
- 持续升温项目
- 值得长期关注项目

## GitHub API 限流说明

本项目使用 GitHub REST API Search Repositories：

```text
GET https://api.github.com/search/repositories
```

请求会携带：

- `Authorization: Bearer ${GITHUB_TOKEN}`
- `Accept: application/vnd.github+json`
- `X-GitHub-Api-Version: 2022-11-28`

如果遇到 HTTP 403 rate limit，程序会输出清晰日志并尽量使用已获得的数据生成报告。如果遇到 HTTP 422，通常表示某个 query 不合法，程序会跳过该关键词并继续执行。

## 项目结构

```text
.
├── run.py
├── requirements.txt
├── README.md
├── config/
│   └── keywords.yml
├── src/
│   ├── github_client.py
│   ├── collector.py
│   ├── scorer.py
│   ├── classifier.py
│   ├── report_daily.py
│   ├── report_weekly.py
│   ├── utils.py
│   └── models.py
├── reports/
│   ├── daily/
│   └── weekly/
└── .github/
    └── workflows/
        └── ai-trends.yml
```

## 示例报告片段

```markdown
# GitHub AI 技术热点日报 - 2026-05-17

生成时间：2026-05-17 08:00:00 Asia/Shanghai

## 今日 Top 项目

### 1. owner/repo

- 地址：https://github.com/owner/repo
- Stars: 12345
- Forks: 678
- Language: Python
- License: MIT
- Categories: LLM, Inference
- Trend Score: 86.35

为什么值得关注：
已有较高社区关注度；命中 llm、inference 等关键词；可归入 LLM、Inference 方向。
```
