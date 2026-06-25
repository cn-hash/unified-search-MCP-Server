# Unified Search MCP Server

> 多平台搜索 + 任意网站逆向分析一体化 MCP Server

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 简介

Unified Search MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的服务，为 AI Agent 提供多平台搜索能力和任意网站逆向分析工具。

集成抖音、小红书、知乎、CSDN 四大平台搜索，同时提供通用的网站分析、数据提取、签名逆向等工具，适用于未知网站的协议恢复场景。

## 功能概览

### 固定平台搜索（5 个工具）

| 工具 | 平台 | 返回数据 |
|------|------|----------|
| `douyin_search` | 抖音 | 视频标题/作者/播放URL/点赞/评论/时长/封面 |
| `xhs_search` | 小红书 | 笔记标题/作者/封面/标签/点赞/收藏/评论 |
| `zhihu_search` | 知乎 | 问题/回答/作者/赞同数/评论数/创建时间 |
| `csdn_search` | CSDN | 文章标题/作者/阅读量/点赞/发布时间 |
| `search_all` | 多平台 | 并行搜索，按平台分组返回汇总结果 |

### 逆向分析工具（5 个工具）

| 工具 | 功能 |
|------|------|
| `recover_protocol` | 一键协议恢复：页面框架识别 → API发现 → 签名检测 → 推荐方案 |
| `analyze_site` | Hook所有XHR/Fetch请求，列出全部API端点及签名头 |
| `hook_network` | 监听指定时长的网络请求，支持关键词过滤 |
| `reverse_signing` | 分析请求签名机制（X-s/a_bogus/anti-content等） |
| `scrape_generic` | CSS选择器通用数据提取，支持text/href/src等字段 |

## 工作原理

```
AI Agent
    ↓ MCP协议 (stdio)
Unified Search MCP Server
    ↓ subprocess
browser-harness CLI
    ↓ CDP协议
用户已登录的 Chrome 浏览器
    ↓ Cookie + 签名JS环境
目标网站 API / DOM
```

所有请求在用户浏览器中执行，自动携带 Cookie 和登录态，签名由浏览器 JS 引擎处理。

## 前置要求

- Python 3.11+
- Chrome 浏览器（已登录目标平台）
- [browser-harness](https://github.com/nousresearch/browser-harness)（CDP 自动化工具）
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## 安装

```bash
# 1. 安装 browser-harness
pip install --user -e ~/browser-harness

# 2. 安装 MCP SDK
pip install mcp

# 3. 克隆本仓库
git clone https://github.com/cn-hash/unified-search-MCP-Server.git
cd unified-search-MCP-Server
```

## 注册到 Hermes Agent

```bash
hermes mcp add unified-search --command python --args "/path/to/server.py"
```

注册后在新 session 中自动加载 10 个工具。

## 使用示例

### 搜索抖音视频

```python
douyin_search(query="风景", max_results=20)
```

### 多平台搜索

```python
search_all(query="Python教程", platforms="zhihu,csdn", max_results=10)
```

### 分析未知网站

```python
# 一键分析
recover_protocol(url="https://example.com")

# 查看API端点
analyze_site(url="https://example.com")

# 分析签名机制
reverse_signing(url="https://example.com", api_url_contains="api")
```

### 通用数据提取

```python
scrape_generic(
    url="https://example.com/products",
    selector="div.product-card",
    fields="text,href,src",
    max_items=50
)
```

## 各平台反爬等级

| 平台 | 反爬等级 | 签名机制 | 采集方案 |
|------|----------|----------|----------|
| 抖音 | 🔴 高 | a_bogus + msToken + 瑞数Cookie | 浏览器DOM提取 + 详情API |
| 小红书 | 🔴 高 | X-s（60KB混淆JS） | 浏览器签名代理 |
| 知乎 | 🟢 低 | 无 | 浏览器直接调REST API |
| CSDN | 🟢 低 | 无 | 浏览器直接调REST API |

## 项目结构

```
unified-search-MCP-Server/
├── README.md              # 本文件
├── LICENSE                # MIT 许可证
├── DISCLAIMER.md          # 免责声明
├── requirements.txt       # Python 依赖
└── server.py              # MCP Server 主文件
```

## ⚠️ 免责声明

**本项目仅供学习和研究使用。**

1. 本项目代码仅用于技术学习、逆向工程研究和合法的数据采集场景。
2. 使用者必须遵守所在国家/地区的法律法规以及目标网站的服务条款（Terms of Service）。
3. **严禁**将本项目用于以下用途：
   - 未经授权大规模采集他人数据
   - 侵犯他人知识产权或隐私权
   - 绕过付费机制获取付费内容
   - 任何形式的网络攻击或恶意行为
   - 违反《网络安全法》《数据安全法》《个人信息保护法》等法律法规的行为
4. 本项目作者不对使用者的任何行为承担责任。使用本项目即表示您同意自行承担一切风险和法律责任。
5. 各平台的 API 和反爬机制可能随时变更，本项目不保证持续可用性。
6. 如有平台方认为本项目侵犯其权益，请联系删除。

**使用者应仅将本项目用于：**
- 个人学习和技术研究
- 合法的数据分析和学术研究
- 已获授权的企业内部数据采集
- 安全测试和渗透测试（需获授权）

## 技术栈

- **MCP**: Model Context Protocol（模型上下文协议）
- **FastMCP**: MCP Python SDK 的高级封装
- **browser-harness**: CDP 浏览器自动化工具
- **Chrome DevTools Protocol (CDP)**: 浏览器调试协议

## 致谢

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Hermes Agent by Nous Research](https://nousresearch.com)

## License

[MIT](LICENSE)
