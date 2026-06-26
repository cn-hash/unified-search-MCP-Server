# 参考项目分析

## js-reverse-mcp (22工具, TypeScript/Node.js)

核心价值: AI-native的JS逆向工程MCP

已整合到Unified Search MCP:
  - list_scripts → 列出页面JS脚本
  - search_scripts → 搜索JS中的关键词
  - get_script_source → 获取JS源码
  - export_request_detail → 导出请求详情
  - take_screenshot → 页面截图

未整合(高价值，未来可加):
  - 断点调试: set_breakpoint_on_text, break_on_xhr, get_paused_info, step
  - WebSocket分析: get_websocket_messages
  - 请求发起链: get_request_initiator
  - 站点数据清理: clear_site_data
  - 反检测: Patchright协议层 + CloakBrowser二进制

关键设计:
  - 零JS注入(MCP层不做Object.defineProperty)
  - CDP静默导航(加载时不激活Network/Debugger)
  - 本地文件I/O桥(save_script_source, outputFile, localFilePath)
  - Profile持久化(登录态跨会话保留)

## search-server (3引擎, Python)

核心价值: 多搜索引擎统一接口

已整合:
  - web_search → Bing/Google/百度搜索(无需API Key)

未整合(需API Key):
  - Brave Search (需API Key)
  - Metaso/秘塔 (逆向接口，不稳定)
  - Bocha/博查 (付费)

关键特性:
  - Brave: location_search(POI搜索)
  - Metaso: scholar_search(学术搜索+AI总结)
  - Bocha: freshness过滤(一天/一周/一月/一年)
