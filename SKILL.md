---
name: unified-search-mcp
description: 统一搜索+逆向MCP Server - 四平台搜索 + 任意网站逆向分析
tags: [mcp, search, reverse-engineering, douyin, xiaohongshu, zhihu, csdn, multi-platform]
category: automation
---

# 统一搜索+逆向 MCP Server

## 10个工具

### 固定平台搜索 (5个)
| 工具 | 平台 | 说明 |
|------|------|------|
| douyin_search | 抖音 | 视频搜索，含播放URL |
| xhs_search | 小红书 | 笔记搜索，含封面/标签 |
| zhihu_search | 知乎 | 问答搜索，含赞同数 |
| csdn_search | CSDN | 技术文章搜索，含阅读量 |
| search_all | 全部 | 多平台并行搜索 |

### 逆向工具链 (5个)
| 工具 | 说明 |
|------|------|
| analyze_site | 分析任意网站API结构，自动发现端点 |
| scrape_generic | CSS选择器通用数据提取 |
| hook_network | 网络请求监听，抓API调用 |
| reverse_signing | 签名机制分析，识别X-s/a_bogus等 |
| recover_protocol | 完整协议恢复工作流 |

## 工作流

```
未知网站
    ↓
recover_protocol(url)     → 自动分析框架/签名/API
    ↓
    ├── 无签名 → scrape_generic() 或 hook_network() 直接抓
    ├── 有签名 → reverse_signing() 分析签名格式
    │            → 浏览器签名代理方案
    └── 已知平台 → 直接调对应search工具
```

## 注册

```bash
hermes mcp add unified-search --command python --args "E:/skill/unified-search-mcp/server.py"
```
