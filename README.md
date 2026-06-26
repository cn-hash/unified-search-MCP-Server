# Unified Search MCP Server

> 🔍 多平台搜索 + 任意网站逆向分析 — 一体化 MCP Server

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Server-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/Tools-16-orange.svg)](#工具列表)

## 这是什么

一个给 AI Agent 用的搜索+逆向工具箱。接入了抖音、小红书、知乎、CSDN 四个平台的搜索，同时提供一套通用的网站分析和 JS 逆向工具，遇到不认识的网站也能快速摸清它的 API 结构和签名机制。

**一句话：让 AI 像一个有经验的爬虫工程师一样工作。**

## 能做什么

### 场景1：搜指定平台

```
"帮我搜抖音上关于风景的视频"        → douyin_search("风景")
"小红书上搜美食笔记"               → xhs_search("美食")
"知乎上搜Python教程"               → zhihu_search("Python教程")
"CSDN上搜Docker部署"              → csdn_search("Docker部署")
"四个平台都搜一下AI"               → search_all("AI")
```

### 场景2：分析未知网站

```
"这个网站用了什么反爬"              → recover_protocol("https://xxx.com")
"帮我看看这个站的API有哪些"         → analyze_site("https://xxx.com")
"它的签名参数是怎么生成的"          → reverse_signing("https://xxx.com")
"帮我提取页面上的商品列表"          → scrape_generic("https://xxx.com", ".product", "text,href,src")
```

### 场景3：JS逆向辅助

```
"这个页面加载了哪些JS"              → list_scripts("https://xxx.com")
"在JS里搜一下encrypt关键字"         → search_scripts("https://xxx.com", "encrypt")
"把那个签名JS的源码拉下来看看"      → get_script_source("https://xxx.com/static/sign.js")
"导出这个API的完整请求详情"         → export_request_detail("https://xxx.com", "api")
```

### 场景4：通用搜索

```
"MCP协议是什么"                    → web_search("MCP协议", engine="bing")
"Python异步编程教程"               → web_search("Python异步编程", engine="baidu")
```

## 工具列表（16个）

### 🎯 平台搜索（5个）

| 工具 | 平台 | 说明 |
|------|------|------|
| `douyin_search` | 抖音 | 搜索视频，返回标题/作者/播放URL/点赞/评论/时长/封面 |
| `xhs_search` | 小红书 | 搜索笔记，返回标题/作者/封面/标签/点赞/收藏 |
| `zhihu_search` | 知乎 | 搜索问答，返回标题/作者/赞同数/评论数 |
| `csdn_search` | CSDN | 搜索文章，返回标题/作者/阅读量/点赞 |
| `search_all` | 全部 | 一次调用搜四个平台，按平台分组返回 |

### 🔬 逆向分析（5个）

| 工具 | 说明 |
|------|------|
| `recover_protocol` | 一键协议恢复：识别框架 → 发现API → 检测签名 → 推荐采集方案 |
| `analyze_site` | Hook所有XHR/Fetch请求，列出全部API端点和签名头 |
| `hook_network` | 按指定时长监听网络请求，支持关键词过滤 |
| `reverse_signing` | 分析签名机制（X-s/a_bogus/anti-content等），返回签名格式 |
| `scrape_generic` | CSS选择器通用提取，支持text/href/src/innerHTML等字段 |

### 📜 JS逆向（4个）

*参考 [js-reverse-mcp](https://github.com/zhizhuodemao/js-reverse-mcp) 设计*

| 工具 | 说明 |
|------|------|
| `list_scripts` | 列出页面加载的所有JS文件（URL/大小/加载耗时） |
| `search_scripts` | 在所有JS脚本中搜索关键词，返回匹配位置和上下文 |
| `get_script_source` | 获取指定JS文件的源代码（前50KB） |
| `export_request_detail` | 导出完整请求详情（请求头/响应头/body/response） |

### 🛠 辅助工具（2个）

| 工具 | 说明 |
|------|------|
| `take_screenshot` | 截取页面截图保存到本地 |
| `web_search` | 通用Web搜索（Bing/Google/百度），无需API Key |

## 工作原理

```
AI Agent (Hermes/Claude/Cursor)
        ↓ MCP协议 (stdio)
Unified Search MCP Server (Python)
        ↓ subprocess
browser-harness CLI
        ↓ CDP协议
用户已登录的 Chrome 浏览器
        ↓ Cookie + JS环境
目标网站 API / DOM
```

核心思路：**让浏览器干活，Python只做调度。**

- 搜索请求在浏览器里发，自动带Cookie，不用处理登录
- 签名由浏览器JS引擎计算，不用逆向（小红书60KB混淆JS？不用管）
- 数据在浏览器里提取精简结果，只传回需要的字段

## 各平台反爬等级

| 平台 | 等级 | 签名机制 | 我们的方案 |
|------|------|----------|----------|
| 抖音 | 🔴 高 | a_bogus + msToken + 瑞数Cookie | DOM提取aweme_id → 详情API |
| 小红书 | 🔴 高 | X-s（60KB混淆JS，每请求唯一） | 浏览器签名代理（拦截API响应） |
| 知乎 | 🟢 低 | 无 | 直接调 /api/v4/search_v3 |
| CSDN | 🟢 低 | 无 | 直接调 /api/v3/search |
| 任意网站 | ❓ | 自动检测 | recover_protocol 一键分析 |

## 安装

### 前置要求

- Python 3.11+
- Chrome 浏览器（已登录目标平台）
- [browser-harness](https://github.com/nousresearch/browser-harness)

### 注册到 Hermes Agent

```bash
hermes mcp add unified-search --command python --args "E:/skill/unified-search-mcp/server.py"
```

注册后新 session 自动加载 16 个工具。

### 其他 MCP 客户端

```json
{
  "mcpServers": {
    "unified-search": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## 项目结构

```
unified-search-MCP-Server/
├── README.md              ← 你在看的这个
├── LICENSE                MIT 许可证
├── DISCLAIMER.md          免责声明（中英文）
├── requirements.txt       Python 依赖
├── server.py              MCP Server 主文件（16个工具）
└── refs/
    └── ANALYSIS.md        参考项目分析报告
```

## 参考项目

- [js-reverse-mcp](https://github.com/zhizhuodemao/js-reverse-mcp) — AI-native JS逆向MCP，22个工具，断点调试+脚本分析+WebSocket分析
- [search-server](https://github.com/fengin/search-server) — 多搜索引擎MCP，支持Brave/秘塔/博查

## ⚠️ 免责声明

**本项目仅供学习和研究使用。**

- ✅ 允许：个人技术学习、学术研究、已授权的安全测试
- ❌ 禁止：未授权数据采集、绕过付费、侵犯隐私、任何违法行为

使用者必须遵守当地法律法规和目标网站服务条款，一切后果自行承担。

详见 [DISCLAIMER.md](DISCLAIMER.md)

## License

[MIT](LICENSE)
