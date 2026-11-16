# 更新日志

## 未发布

- 新增 SRT 字幕导出：DashScope 云端识别返回的句子级时间戳会被保留并转为 SubRip 字幕。Web 页面在结果区提供「下载 .srt」按钮（仅在存在时间戳时显示），CLI 新增 `--format srt`，API 响应新增 `srt` 与 `srt_available` 字段。字幕按词边界拆分过长的句子，保证时间单调递增，文件以 UTF-8 BOM 写出以兼容常见播放器；本地 Whisper / SenseVoice 不提供时间戳，此时不显示字幕下载。
- 新增 `DASHSCOPE_BASE_URL` 配置，支持私有化部署或代理访问 DashScope 原生 API；留空使用 SDK 默认地址。
- 修复 Web 配置页在 Windows 上保存配置总是失败的问题（只读句柄 `fsync` 触发 `EBADF`）。

## 1.0.0 — 2026-10-16

首个正式版本，Git 标签为 `v1.0`。

- 规范化包元数据、MIT 许可、CLI/Web 命令入口与 wheel 资源清单。
- 将 Whisper 作为可选依赖，默认安装避免引入大型机器学习依赖。
- Web API 支持 Bearer 或 `X-API-Token` 认证；健康检查 `/api/health` 不要求令牌。
- Web API 提取为同步请求；长转写期间客户端需等待响应，超出并发上限时返回 429，不提供进度查询。
- OSS 默认使用限时签名 URL 支持私有 Bucket；详见 [OSS 配置指南](docs/OSS_GUIDE.md)。
- 新增独立的 `FFMPEG_TIMEOUT` 和经令牌保护的 `WEB_PUBLIC_ORIGIN` 配置说明；媒体下载的初始 URL 与重定向目标受平台/CDN 域名校验。
- 默认测试不连接外部服务；真实 OSS 测试须显式启用。
- 修复分享页 HTTP 200 但间歇性缺失视频详情的情况，复用会话进行有限重试并区分无视频、访问拒绝和数据异常。
- 新增 `DOWNLOAD_TIMEOUT=300`，将媒体下载总时限与 `REQUEST_TIMEOUT` 的连接/读取等待超时分开，避免持续下载的视频被 30 秒时限中断。
- 补充抖音冷媒体节点 `idouyinvod.com` 的域名校验支持，修复部分精选视频重定向到该 CDN 后被误拒绝的问题。
- Whisper 关闭跨窗口文本提示并启用 beam search，减少错误上下文形成的循环重复；保留正常口语重复与低置信度重试，模型切换时释放旧缓存。
- 新增可选 `local-chinese` 依赖与 SenseVoiceSmall 中文本地引擎，校验并缓存官方 int8 模型、按低能量位置分段处理长音频，输出标点；权重使用独立模型协议。
- Web 配置页支持选择本地引擎及 Whisper 模型，说明下载大小与速度取舍；新增 `LOCAL_ASR_ENGINE` 和 Docker 构建选项 `INSTALL_CHINESE_ASR`。
- 精简 Web 顶部与移动布局，折叠可选访问令牌，提供完整文本阅读、复制、TXT 下载和字数提示；更新 README 的引擎安装、启动、常见问题与页面预览。
