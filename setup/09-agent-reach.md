# 可选：其他来源

微信和飞书继续用已有连接器。网页、GitHub、RSS、社交、视频或音频优先用宿主可用且获授权的工具；不预设具体工具已经安装或当前仍可用。

视频/音频需要字幕或转录，存 `.raw/transcripts/`；GitHub 存 README 和 metadata；RSS 存 `.raw/rss/`；社交帖存 `.raw/social/`；普通网页存 `.raw/webfetch/`。失败或截断要明确说明，不能按标题编全文。

Agent-Reach 可以作为额外路由选择，按其当前官方说明安装和验证，本包不复制登录状态、cookie 或 token。任何新订阅、定时任务或对外发送都需要对应任务授权。
