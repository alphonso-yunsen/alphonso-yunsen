# 星空主页维护

## 视觉与组件

保留原创动漫横幅，统一使用午夜蓝底色、薰衣草紫标题、浅青色点缀和 20px 圆角。配色集中在 `profile-theme.json`。统计卡片使用 440px 自然宽度，在窄屏自动换行。

| 参考项目 | 本主页的采用方式 |
| --- | --- |
| [Platane/snk](https://github.com/Platane/snk) | 实际运行其 SVG Action，定制青色蛇身、紫色贡献格和星空卡片外框 |
| [lowlighter/metrics](https://github.com/lowlighter/metrics) | 借鉴仪表盘布局，用自有轻量脚本绘制公开数据摘要 |
| [github-profile-summary-cards](https://github.com/vn7n24fzkq/github-profile-summary-cards) | 借鉴等高卡片组织，统一字体、颜色和留白 |
| [readme-typing-svg](https://github.com/DenverCoder1/readme-typing-svg) | 借鉴打字效果，采用仓库内原生 SVG 动画，支持减少动态效果偏好 |
| [github-readme-activity-graph](https://github.com/Ashutosh00710/github-readme-activity-graph) | 借鉴近 31 天曲线，自有脚本绘制真实每日贡献数量 |
| [skill-icons](https://github.com/tandpfun/skill-icons) | 使用官方图标服务的深色图标，仅列本人确认的工具 |
| [github-profile-views-counter](https://github.com/antonkomarev/github-profile-views-counter) | 使用 Komarev 页尾徽章，不设置虚增基数；这是图片加载计数，不是独立访客数 |

除 snk Action、图标与访问徽章外，其他项目作为设计参考，未复制其实现，也不依赖其在线统计服务。

## 自动刷新

`.github/workflows/profile.yml` 每天 00:23 UTC（北京时间 08:23）运行；也可以在 Actions 页手动运行 **Refresh starfield profile**。GitHub 定时任务可能延迟；以最近成功运行和卡片日期为准。仓库长期无活动时，GitHub 可能暂停定时工作流。

- 使用本公开主页仓库的短期 `GITHUB_TOKEN`，无需新增个人 Token。
- REST 仅读取公开用户资料和公开仓库；GraphQL 仅请求日期及贡献数量，不请求仓库名或提交内容。
- 年度贪吃蛇与 31 天图的统计周期不同。贡献数量遵循 GitHub 日历口径，不等于 Commit 数；已公开的匿名私有贡献可能出现在日历中。
- Stars 是自有、非 Fork 公开仓库收到的星标，不是本人收藏数。
- 不保存原始 API 响应；`generated/profile.json` 只保留渲染所需的公开摘要和日计数。
- 所有步骤成功后才提交生成物。失败时保留上次图片，Actions 会留下失败记录。
- 更新提交使用 GitHub Actions 机器人身份，不伪造个人贡献。
- `generated/` 中的图可以直接通过 GitHub 加载；头像、横幅和私有研究项目互不依赖。

## 编辑

修改介绍：`README.md`。修改图表和终端：`scripts/render_profile.py`。调整蛇配色时同时更新工作流的 `outputs` 参数；`profile-theme.json` 中的 `snake` 保存对应调色板供参考。图标需修改 README 的 `skillicons.dev` 参数。

生成脚本仅依赖 Python 标准库。第三方 Action 固定到已审核版本的 commit SHA。发布前检查 SVG 可解析、图片可加载、窄屏无横向溢出及公开内容范围。
