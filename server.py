#!/usr/bin/env python3
"""
统一搜索 MCP Server
==================
整合抖音、小红书、知乎、CSDN四平台搜索能力为一个MCP服务。

工具:
  - douyin_search: 抖音视频搜索
  - xhs_search: 小红书笔记搜索
  - zhihu_search: 知乎问答搜索
  - csdn_search: CSDN技术文章搜索
  - search_all: 多平台并行搜索

依赖: browser-harness (pip install --user -e ~/browser-harness)
"""

import json
import logging
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("search-mcp")

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="unified-search",
    instructions="多平台搜索工具：抖音视频、小红书笔记、知乎问答、CSDN技术文章。需要已登录的Chrome浏览器运行中。",
)


# ============================================================
# browser-harness runner
# ============================================================

def run_bh(script: str, timeout: int = 120) -> str:
    proc = subprocess.run(
        ["browser-harness"],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"browser-harness error: {proc.stderr[-300:]}")
    return proc.stdout.strip()


# ============================================================
# 抖音搜索
# ============================================================

DOUYIN_SCRIPT = '''
import time, json, urllib.parse
from browser_harness.helpers import cdp, js

query = "__QUERY__"
max_results = __MAX_RESULTS__
encoded = urllib.parse.quote(query)

# Install persistent hooks
cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__dyCapture = [];
    var _o = XMLHttpRequest.prototype.open, _s = XMLHttpRequest.prototype.send, _h = XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open = function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments);};
    XMLHttpRequest.prototype.setRequestHeader = function(k,v){this.__h[k]=v;return _h.apply(this,arguments);};
    XMLHttpRequest.prototype.send = function(b){var self=this;this.addEventListener('load',function(){if(self.__u&&self.__u.includes('aweme/v1/web/aweme/detail')){window.__dyCapture.push({url:self.__u,resp:self.responseText.substring(0,50000)})}});return _s.apply(this,arguments);};
})()
\"\"\")

js("window.location.href='https://www.douyin.com/search/"+encoded+"?type=video'")
time.sleep(6)

# Scroll if needed
if max_results > 20:
    for i in range(15):
        if int(js("document.querySelectorAll('.search-result-card').length")) >= max_results: break
        js("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(2)

# Extract aweme_ids
ids = json.loads(js("(function(){var c=document.querySelectorAll('.search-result-card');var s={};var r=[];c.forEach(function(e){var l=e.querySelector('a[href*=\"/video/\"]');if(l){var m=l.href.match(/video\\/(\\d+)/);if(m&&!s[m[1]]){s[m[1]]=true;r.push(m[1])}}});return JSON.stringify(r)})()"))[:max_results]

# Get details
all_items = []
for aid in ids:
    detail = js("(function(){return new Promise(function(r){var x=new XMLHttpRequest();x.open('GET','/aweme/v1/web/aweme/detail/?aweme_id="+aid+"&device_platform=webapp&aid=6383&channel=channel_pc_web');x.onload=function(){try{var d=JSON.parse(x.responseText);var a=d.aweme_detail;if(!a){r('{}');return}var v=a.video||{};var p=v.play_addr||{};r(JSON.stringify({aweme_id:a.aweme_id,desc:a.desc||'',author:a.author?a.author.nickname:'',duration_ms:v.duration||0,play_url:(p.url_list||[])[0]||'',cover:(v.cover&&v.cover.url_list||[])[0]||'',digg_count:(a.statistics||{}).digg_count||0,comment_count:(a.statistics||{}).comment_count||0,share_count:(a.statistics||{}).share_count||0}))}catch(e){r('{}')}};x.send()})})()")
    try:
        item = json.loads(detail)
        if item.get("aweme_id"):
            all_items.append(item)
    except: pass
    time.sleep(0.3)

print(json.dumps(all_items, ensure_ascii=False))
'''

@mcp.tool()
def douyin_search(query: str, max_results: int = 20) -> str:
    """
    搜索抖音视频，获取视频元数据和播放URL。

    Args:
        query: 搜索关键词
        max_results: 最大结果数(默认20)

    Returns:
        JSON数组，每项包含: aweme_id, desc, author, duration_ms, play_url, cover, digg_count, comment_count
    """
    try:
        script = DOUYIN_SCRIPT.replace("__QUERY__", query.replace('"', '\\"')).replace("__MAX_RESULTS__", str(max_results))
        raw = run_bh(script, timeout=180)
        items = json.loads(raw)
        for item in items:
            dur = item.get("duration_ms", 0) / 1000
            item["duration_str"] = f"{int(dur//60):02d}:{int(dur%60):02d}"
        return json.dumps({"platform": "douyin", "count": len(items), "items": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "platform": "douyin"}, ensure_ascii=False)


# ============================================================
# 小红书搜索
# ============================================================

XHS_SCRIPT = '''
import time, json, urllib.parse
from browser_harness.helpers import cdp, js

query = "__QUERY__"
max_results = __MAX_RESULTS__
encoded = urllib.parse.quote(query)

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__xhsData = { results: [] };
    var _o = XMLHttpRequest.prototype.open, _s = XMLHttpRequest.prototype.send, _h = XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open = function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments);};
    XMLHttpRequest.prototype.setRequestHeader = function(k,v){this.__h[k]=v;return _h.apply(this,arguments);};
    XMLHttpRequest.prototype.send = function(b){var self=this;this.addEventListener('load',function(){if(self.__u&&self.__u.includes('search/notes')){try{var d=JSON.parse(self.responseText);if(d.success&&d.data&&d.data.items){window.__xhsData.results.push({items:d.data.items,has_more:d.data.has_more})}}catch(e){}}});return _s.apply(this,arguments);};
})()
\"\"\")

js("window.location.href='https://www.xiaohongshu.com/search_result?keyword="+encoded+"&source=web_explore_feed'")
time.sleep(8)

if max_results > 20:
    for i in range(15):
        js("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(2)
        total = js("(function(){var t=0;if(window.__xhsData)window.__xhsData.results.forEach(function(r){t+=r.items.length});return t})()")
        if int(total) >= max_results: break

result = js("(function(){var all=[];var seen={};if(window.__xhsData)window.__xhsData.results.forEach(function(r){(r.items||[]).forEach(function(item){if(seen[item.id])return;seen[item.id]=true;var nc=item.note_card||{};var u=nc.user||{};var it=nc.interact_info||{};var img=(nc.image_list||[])[0]||{};all.push({note_id:item.id,title:nc.display_title||'',desc:(nc.desc||'').substring(0,300),type:nc.type||'normal',author:u.nick_name||'',liked_count:it.liked_count||'0',collected_count:it.collected_count||'0',comment_count:it.comment_count||'0',cover:((img.info_list||[])[0]||{}).url||'',tags:(nc.tag_list||[]).map(function(t){return t.name||''}),url:'https://www.xiaohongshu.com/explore/'+item.id})})});return JSON.stringify(all)})()")
print(result)
'''

@mcp.tool()
def xhs_search(query: str, max_results: int = 20) -> str:
    """
    搜索小红书笔记，获取标题、作者、点赞、封面等数据。

    Args:
        query: 搜索关键词
        max_results: 最大结果数(默认20)

    Returns:
        JSON数组，每项包含: note_id, title, desc, author, liked_count, collected_count, cover, tags, url
    """
    try:
        script = XHS_SCRIPT.replace("__QUERY__", query.replace('"', '\\"')).replace("__MAX_RESULTS__", str(max_results))
        raw = run_bh(script, timeout=180)
        items = json.loads(raw)
        return json.dumps({"platform": "xiaohongshu", "count": len(items), "items": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "platform": "xiaohongshu"}, ensure_ascii=False)


# ============================================================
# 知乎搜索
# ============================================================

ZHIHU_SCRIPT = '''
import time, json, urllib.parse
from browser_harness.helpers import js

query = urllib.parse.quote("__QUERY__")
max_results = __MAX_RESULTS__
all_items = []
offset = 0

while len(all_items) < max_results:
    limit = min(20, max_results - len(all_items))
    url = "/api/v4/search_v3?t=general&q="+query+"&correction=1&offset="+str(offset)+"&limit="+str(limit)+"&search_source=Normal"
    result = js("(function(){return new Promise(function(r){var x=new XMLHttpRequest();x.open('GET','"+url+"');x.onload=function(){try{var d=JSON.parse(x.responseText);var items=(d.data||[]).filter(function(i){return i.type==='search_result'});var res=items.map(function(t){var o=t.object||{};var a=o.author||{};var q=o.question||{};return{type:o.type||'',id:o.id||'',title:q.title||o.title||'',excerpt:(o.excerpt||'').substring(0,300),author:a.name||'',voteup_count:o.voteup_count||0,comment_count:o.comment_count||0,created_time:o.created_time||0,url:o.url||'',answer_count:q.answer_count||0}});r(JSON.stringify({items:res,is_end:d.paging?d.paging.is_end:true}))}catch(e){r(JSON.stringify({error:e.message}))}};x.onerror=function(){r(JSON.stringify({error:'network'}))};x.send()})})()")
    data = json.loads(result)
    if data.get("error"): break
    items = data.get("items", [])
    if not items: break
    all_items.extend(items)
    if data.get("is_end", True): break
    offset += len(items)
    time.sleep(0.5)

print(json.dumps(all_items[:max_results], ensure_ascii=False))
'''

@mcp.tool()
def zhihu_search(query: str, max_results: int = 20) -> str:
    """
    搜索知乎问答，获取标题、作者、赞同数等数据。

    Args:
        query: 搜索关键词
        max_results: 最大结果数(默认20)

    Returns:
        JSON数组，每项包含: id, title, excerpt, author, voteup_count, comment_count, created_time, url
    """
    try:
        script = ZHIHU_SCRIPT.replace("__QUERY__", query.replace('"', '\\"')).replace("__MAX_RESULTS__", str(max_results))
        raw = run_bh(script, timeout=120)
        items = json.loads(raw)
        for item in items:
            ct = item.get("created_time", 0)
            if ct:
                item["created_time_str"] = datetime.fromtimestamp(ct).strftime("%Y-%m-%d")
        return json.dumps({"platform": "zhihu", "count": len(items), "items": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "platform": "zhihu"}, ensure_ascii=False)


# ============================================================
# CSDN搜索
# ============================================================

CSDN_SCRIPT = '''
import time, json, urllib.parse
from browser_harness.helpers import js

query = urllib.parse.quote("__QUERY__")
max_results = __MAX_RESULTS__
all_items = []
page = 1

while len(all_items) < max_results:
    url = "/api/v3/search?q="+query+"&t=all&p="+str(page)+"&s=0&tm=0&lv=-1&ft=0&ia=1"
    result = js("(function(){return new Promise(function(r){var x=new XMLHttpRequest();x.open('GET','"+url+"');x.onload=function(){try{var d=JSON.parse(x.responseText);var items=d.result_vos||[];var res=items.map(function(i){return{title:(i.title||'').replace(/<[^>]+>/g,''),url:i.url||'',description:(i.description||'').replace(/<[^>]+>/g,'').substring(0,300),nickname:i.nickname||'',view:parseInt(i.view)||0,comment:parseInt(i.comment)||0,digg:parseInt(i.digg)||0,type:i.type||'',created_at:i.created_at||''}});r(JSON.stringify({items:res}))}catch(e){r(JSON.stringify({error:e.message}))}};x.onerror=function(){r(JSON.stringify({error:'network'}))};x.send()})})()")
    data = json.loads(result)
    if data.get("error"): break
    items = data.get("items", [])
    if not items: break
    all_items.extend(items)
    if len(items) < 20: break
    page += 1
    time.sleep(0.5)

print(json.dumps(all_items[:max_results], ensure_ascii=False))
'''

@mcp.tool()
def csdn_search(query: str, max_results: int = 20) -> str:
    """
    搜索CSDN技术文章，获取标题、作者、阅读量等数据。

    Args:
        query: 搜索关键词
        max_results: 最大结果数(默认20)

    Returns:
        JSON数组，每项包含: title, url, description, nickname, view, comment, digg, type, created_at
    """
    try:
        script = CSDN_SCRIPT.replace("__QUERY__", query.replace('"', '\\"')).replace("__MAX_RESULTS__", str(max_results))
        raw = run_bh(script, timeout=120)
        items = json.loads(raw)
        return json.dumps({"platform": "csdn", "count": len(items), "items": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "platform": "csdn"}, ensure_ascii=False)


# ============================================================
# 多平台搜索
# ============================================================

@mcp.tool()
def search_all(query: str, platforms: str = "douyin,xhs,zhihu,csdn", max_results: int = 10) -> str:
    """
    多平台搜索，返回各平台汇总结果。

    Args:
        query: 搜索关键词
        platforms: 逗号分隔的平台列表，可选: douyin, xhs, zhihu, csdn
        max_results: 每个平台的最大结果数(默认10)

    Returns:
        JSON对象，按平台分组的结果
    """
    platform_list = [p.strip() for p in platforms.split(",")]
    results = {}

    for platform in platform_list:
        try:
            if platform == "douyin":
                results["douyin"] = json.loads(douyin_search(query, max_results))
            elif platform == "xhs":
                results["xhs"] = json.loads(xhs_search(query, max_results))
            elif platform == "zhihu":
                results["zhihu"] = json.loads(zhihu_search(query, max_results))
            elif platform == "csdn":
                results["csdn"] = json.loads(csdn_search(query, max_results))
            else:
                results[platform] = {"error": f"未知平台: {platform}"}
        except Exception as e:
            results[platform] = {"error": str(e)}

    total = sum(r.get("count", 0) for r in results.values() if isinstance(r, dict))
    return json.dumps({"query": query, "total": total, "platforms": results}, ensure_ascii=False, indent=2)


# ============================================================
# 逆向工具链 - 处理任意网站
# ============================================================

_ANALYZE_SITE_JS = """
import time, json
from browser_harness.helpers import cdp, js

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__apis = [];
    var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send,_h=XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open=function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments)};
    XMLHttpRequest.prototype.setRequestHeader=function(k,v){this.__h[k]=v;return _h.apply(this,arguments)};
    XMLHttpRequest.prototype.send=function(b){var self=this;this.addEventListener('load',function(){window.__apis.push({method:self.__m,url:self.__u,body:b?String(b).substring(0,300):'',status:self.status,headers:Object.keys(self.__h).filter(function(k){return k.toLowerCase().startsWith('x-')}),resp_preview:self.responseText.substring(0,500)})});return _s.apply(this,arguments)};
    var _f=window.fetch;window.fetch=function(i,init){var url=typeof i==='string'?i:(i.url||'');return _f.apply(this,arguments).then(function(r){window.__apis.push({method:(init&&init.method)||'GET',url:url,status:r.status});return r})};
})()
\"\"\")

js("window.location.href=__TARGET_URL__")
time.sleep(8)
js("window.scrollTo(0,document.body.scrollHeight)")
time.sleep(3)

title = js("document.title")
apis = json.loads(js("JSON.stringify(window.__apis||[])"))
api_calls = [a for a in apis if not any(a['url'].endswith(ext) for ext in ['.js','.css','.png','.jpg','.gif','.svg','.woff','.ico'])]

result = {"title": title, "url": "__TARGET_URL__", "api_count": len(api_calls), "apis": []}
for a in api_calls[:30]:
    result["apis"].append({"method": a.get("method",""), "url": a["url"][:200], "status": a.get("status"), "has_sign_headers": len(a.get("headers",[])) > 0, "sign_headers": a.get("headers",[]), "body_preview": a.get("body","")[:200], "resp_preview": a.get("resp_preview","")[:300]})

print(json.dumps(result, ensure_ascii=False))
"""

_SCRAPE_GENERIC_JS = """
import time, json
from browser_harness.helpers import js

js("window.location.href=__TARGET_URL__")
time.sleep(6)
for i in range(3):
    js("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(1.5)

result = js("(function(){var els=document.querySelectorAll('__SELECTOR__');var fields=[__FIELDS__];var res=[];var max=__MAX__;for(var i=0;i<Math.min(els.length,max);i++){var el=els[i];var item={};fields.forEach(function(f){if(f==='text')item.text=el.textContent.trim().substring(0,200);else if(f==='href')item.href=el.href||el.getAttribute('href')||'';else if(f==='src')item.src=el.src||el.getAttribute('src')||'';else if(f==='innerHTML')item.innerHTML=el.innerHTML.substring(0,500);else if(f==='title')item.title=el.title||el.getAttribute('title')||'';else if(f==='class')item.class=el.className;else item[f]=el.getAttribute(f)||''});res.push(item)}return JSON.stringify(res)})()")
print(result)
"""

_HOOK_NETWORK_JS = """
import time, json
from browser_harness.helpers import cdp, js

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__netLog = [];
    var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send,_h=XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open=function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments)};
    XMLHttpRequest.prototype.setRequestHeader=function(k,v){this.__h[k]=v;return _h.apply(this,arguments)};
    XMLHttpRequest.prototype.send=function(b){var self=this;this.addEventListener('load',function(){window.__netLog.push({method:self.__m,url:self.__u,body:b?String(b).substring(0,500):'',status:self.status,headers:JSON.parse(JSON.stringify(self.__h)),resp:self.responseText.substring(0,1000)})});return _s.apply(this,arguments)};
    var _f=window.fetch;window.fetch=function(i,init){var url=typeof i==='string'?i:(i.url||'');return _f.apply(this,arguments).then(function(r){var c=r.clone();c.text().then(function(t){window.__netLog.push({method:(init&&init.method)||'GET',url:url,status:r.status,body:init&&init.body?String(init.body).substring(0,500):'',resp:t.substring(0,1000)})});return r})};
})()
\"\"\")

js("window.location.href=__TARGET_URL__")
time.sleep(__DURATION__)
js("window.scrollTo(0,document.body.scrollHeight)")
time.sleep(2)

logs = json.loads(js("JSON.stringify(window.__netLog||[])"))
filter_kw = "__FILTER__"
if filter_kw:
    logs = [l for l in logs if filter_kw in l.get('url','')]
logs = [l for l in logs if not any(l['url'].endswith(ext) for ext in ['.js','.css','.png','.jpg','.gif','.svg','.woff','.ico'])]

print(json.dumps({"count": len(logs), "requests": logs[:50]}, ensure_ascii=False))
"""

_REVERSE_SIGNING_JS = """
import time, json
from browser_harness.helpers import cdp, js

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__signedReqs = [];
    var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send,_h=XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open=function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments)};
    XMLHttpRequest.prototype.setRequestHeader=function(k,v){this.__h[k]=v;return _h.apply(this,arguments)};
    XMLHttpRequest.prototype.send=function(b){var self=this;var signHeaders={};var signKeys=['x-s','x-t','x-s-common','x-bogus','a_bogus','x-signature','x-xt','anti-content','x-s-token'];for(var k in this.__h){if(signKeys.indexOf(k.toLowerCase())!==-1||k.toLowerCase().startsWith('x-s'))signHeaders[k]=this.__h[k]}if(Object.keys(signHeaders).length>0){window.__signedReqs.push({method:self.__m,url:self.__u,body:b?String(b).substring(0,500):'',signHeaders:signHeaders,allHeaderKeys:Object.keys(self.__h)})}return _s.apply(this,arguments)};
})()
\"\"\")

js("window.location.href=__TARGET_URL__")
time.sleep(8)
js("window.scrollTo(0,document.body.scrollHeight)")
time.sleep(3)

reqs = json.loads(js("JSON.stringify(window.__signedReqs||[])"))
filter_kw = "__FILTER__"
if filter_kw:
    reqs = [r for r in reqs if filter_kw in r.get('url','')]

all_sign_keys = set()
for r in reqs:
    for k in r.get('signHeaders', {}):
        all_sign_keys.add(k)

analysis = {"sign_header_names": list(all_sign_keys), "total_signed_requests": len(reqs)}
if reqs:
    sample = reqs[0].get('signHeaders', {})
    for k, v in sample.items():
        if v.startswith('XYS_'): analysis["format_hint"] = "XHS-style: prefix + base64"
        elif len(v) > 50 and '/' in v: analysis["format_hint"] = "base64-encoded signature"
        elif v.isdigit(): analysis["format_hint"] = "timestamp (ms)"

print(json.dumps({"signed_requests": reqs[:10], "analysis": analysis}, ensure_ascii=False, indent=2))
"""

_RECOVER_PROTOCOL_JS = """
import time, json
from browser_harness.helpers import cdp, js

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__protoRecovery = {apis:[], signed:[]};
    var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send,_h=XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open=function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments)};
    XMLHttpRequest.prototype.setRequestHeader=function(k,v){this.__h[k]=v;return _h.apply(this,arguments)};
    XMLHttpRequest.prototype.send=function(b){var self=this;var signH={};for(var k in this.__h){if(k.toLowerCase().startsWith('x-')&&k.toLowerCase()!=='x-requested-with')signH[k]=this.__h[k]}window.__protoRecovery.apis.push({m:self.__m,u:self.__u,s:self.status,b:b?String(b).substring(0,200):''});if(Object.keys(signH).length>0)window.__protoRecovery.signed.push({u:self.__u,sh:signH});return _s.apply(this,arguments)};
})()
\"\"\")

js("window.location.href=__TARGET_URL__")
time.sleep(8)

title = js("document.title")
framework = js("(function(){if(window.__NUXT__)return'nuxt';if(window.__NEXT_DATA__)return'next';if(window.React||document.querySelector('[data-reactroot]'))return'react';if(window.Vue||document.querySelector('[data-v-]'))return'vue';if(window.angular)return'angular';return'unknown'})()")
inputs = json.loads(js("(function(){var r=[];document.querySelectorAll('input,div[contenteditable]').forEach(function(e){var rect=e.getBoundingClientRect();if(rect.width>100)r.push({tag:e.tagName,type:e.type,placeholder:e.placeholder,cls:(typeof e.className==='string'?e.className:'').substring(0,50),x:Math.round(rect.x+rect.width/2),y:Math.round(rect.y+rect.height/2)})});return JSON.stringify(r)})()"))

js("window.scrollTo(0,document.body.scrollHeight)")
time.sleep(3)

data = json.loads(js("JSON.stringify(window.__protoRecovery||{})"))
apis = [a for a in data.get('apis',[]) if not any(a['u'].endswith(ext) for ext in ['.js','.css','.png','.jpg','.svg','.woff','.ico'])]
signed = data.get('signed', [])

approach = "browser_dom"
if signed:
    sign_keys = set()
    for s in signed:
        for k in s.get('sh',{}):
            sign_keys.add(k)
    if any('x-s' in k.lower() for k in sign_keys): approach = "xhs_signing_proxy"
    elif any('bogus' in k.lower() for k in sign_keys): approach = "douyin_style_browser"
    else: approach = "signing_reverse_needed"
elif len(apis) > 5: approach = "api_direct"

result = {
    "site_info": {"title": title, "framework": framework, "url": "__TARGET_URL__"},
    "search_inputs": inputs,
    "api_count": len(apis),
    "apis_sample": apis[:15],
    "signing": {"has_signing": len(signed) > 0, "signed_count": len(signed), "sign_headers": list(set(k for s in signed for k in s.get('sh',{})))},
    "recommended_approach": approach
}
print(json.dumps(result, ensure_ascii=False, indent=2))
"""


@mcp.tool()
def analyze_site(url: str) -> str:
    """分析任意网站的API结构。Hook所有XHR/Fetch请求，返回API端点列表。"""
    try:
        script = _ANALYZE_SITE_JS.replace("__TARGET_URL__", "'" + url + "'")
        return run_bh(script, timeout=30)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def scrape_generic(url: str, selector: str = "a", fields: str = "text,href", max_items: int = 20) -> str:
    """通用网页数据提取。用CSS选择器从任意URL提取数据。"""
    try:
        field_list = [f.strip() for f in fields.split(",")]
        field_js = ",".join(["'" + f + "'" for f in field_list])
        script = (_SCRAPE_GENERIC_JS
                  .replace("__TARGET_URL__", "'" + url + "'")
                  .replace("__SELECTOR__", selector)
                  .replace("__FIELDS__", field_js)
                  .replace("__MAX__", str(max_items)))
        raw = run_bh(script, timeout=30)
        items = json.loads(raw)
        return json.dumps({"url": url, "selector": selector, "count": len(items), "items": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def hook_network(url: str, duration_seconds: int = 10, filter_keyword: str = "") -> str:
    """在指定页面安装网络监听Hook，返回捕获的API请求。"""
    try:
        script = (_HOOK_NETWORK_JS
                  .replace("__TARGET_URL__", "'" + url + "'")
                  .replace("__DURATION__", str(duration_seconds))
                  .replace("__FILTER__", filter_keyword))
        return run_bh(script, timeout=duration_seconds + 30)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def reverse_signing(url: str, api_url_contains: str = "") -> str:
    """分析目标网站的请求签名机制，返回签名参数格式和模式。"""
    try:
        script = (_REVERSE_SIGNING_JS
                  .replace("__TARGET_URL__", "'" + url + "'")
                  .replace("__FILTER__", api_url_contains))
        return run_bh(script, timeout=30)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def recover_protocol(url: str) -> str:
    """完整协议恢复: 页面分析 → API发现 → 签名识别 → 推荐方案。"""
    try:
        script = _RECOVER_PROTOCOL_JS.replace("__TARGET_URL__", "'" + url + "'")
        return run_bh(script, timeout=30)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ============================================================
# JS逆向分析工具 (参考 js-reverse-mcp)
# ============================================================

_LIST_SCRIPTS_JS = """
import time, json
from browser_harness.helpers import js

result = js("(function(){var scripts=performance.getEntriesByType('resource').filter(function(e){return e.initiatorType==='script'});var res=scripts.map(function(s){return{url:s.name,size:s.transferSize,duration:Math.round(s.duration)}});return JSON.stringify(res)})()")
print(result)
"""

_SEARCH_SCRIPTS_JS = """
import time, json
from browser_harness.helpers import js

keyword = "__KEYWORD__"
result = js("(function(){return new Promise(function(resolve){var scripts=document.querySelectorAll('script[src]');var results=[];var pending=scripts.length;if(pending===0){resolve(JSON.stringify([]));return}scripts.forEach(function(s){var url=s.src;var x=new XMLHttpRequest();x.open('GET',url);x.onload=function(){var text=x.responseText;var matches=[];var idx=0;while((idx=text.indexOf('__KEYWORD__',idx))!==-1){matches.push({position:idx,context:text.substring(Math.max(0,idx-50),idx+50).replace(/\\n/g,' ')});idx++;if(matches.length>=5)break}if(matches.length>0)results.push({url:url,match_count:matches.length,matches:matches});pending--;if(pending===0)resolve(JSON.stringify(results))};x.onerror=function(){pending--;if(pending===0)resolve(JSON.stringify(results))};x.send()})})()")

print(result)
"""

_GET_SCRIPT_SOURCE_JS = """
import time, json
from browser_harness.helpers import js

script_url = "__SCRIPT_URL__"
result = js("(function(){return new Promise(function(resolve){var x=new XMLHttpRequest();x.open('GET','__SCRIPT_URL__');x.onload=function(){resolve(JSON.stringify({url:'__SCRIPT_URL__',size:x.responseText.length,source:x.responseText.substring(0,50000)}))};x.onerror=function(){resolve(JSON.stringify({error:'failed to fetch script'}))};x.send()})})()")
print(result)
"""

_EXPORT_REQUEST_JS = """
import time, json
from browser_harness.helpers import cdp, js

cdp("Page.addScriptToEvaluateOnNewDocument", source=\"\"\"
(function() {
    window.__reqDetail = [];
    var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send,_h=XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.open=function(m,u){this.__m=m;this.__u=u;this.__h={};return _o.apply(this,arguments)};
    XMLHttpRequest.prototype.setRequestHeader=function(k,v){this.__h[k]=v;return _h.apply(this,arguments)};
    XMLHttpRequest.prototype.send=function(b){var self=this;this.addEventListener('load',function(){window.__reqDetail.push({method:self.__m,url:self.__u,body:b?String(b):'',status:self.status,headers:JSON.parse(JSON.stringify(self.__h)),responseHeaders:self.getAllResponseHeaders(),responseType:self.responseType,responseSize:self.responseText?self.responseText.length:0,responsePreview:self.responseText?self.responseText.substring(0,2000):''})});return _s.apply(this,arguments)};
})()
\"\"\")

js("window.location.href=__TARGET_URL__")
time.sleep(8)
js("window.scrollTo(0,document.body.scrollHeight)")
time.sleep(3)

reqs = json.loads(js("JSON.stringify(window.__reqDetail||[])"))
filter_kw = "__FILTER__"
if filter_kw:
    reqs = [r for r in reqs if filter_kw in r.get('url','')]
reqs = [r for r in reqs if not any(r['url'].endswith(ext) for ext in ['.js','.css','.png','.jpg','.gif','.svg','.woff','.ico'])]

print(json.dumps({"count": len(reqs), "requests": reqs[:30]}, ensure_ascii=False, indent=2))
"""

_SCREENSHOT_JS = """
import time
from browser_harness.helpers import js

js("window.scrollTo(0,0)")
time.sleep(1)

title = js("document.title").replace("/","_").replace("\\\\","_").replace(":","_")[:30]
path = "E:/skill/screenshot_" + title + ".png"

from browser_harness.helpers import cdp
cdp("Page.captureScreenshot", format="png")

# Use browser-harness built-in
capture_screenshot(path)
print(json.dumps({"path": path, "title": title}))
"""

_WEB_SEARCH_JS = """
import time, json, urllib.parse
from browser_harness.helpers import js

query = urllib.parse.quote("__QUERY__")
engine = "__ENGINE__"

if engine == "bing":
    url = "https://www.bing.com/search?q=" + query
elif engine == "google":
    url = "https://www.google.com/search?q=" + query
elif engine == "baidu":
    url = "https://www.baidu.com/s?wd=" + query
else:
    url = "https://www.bing.com/search?q=" + query

js("window.location.href='" + url + "'")
time.sleep(6)

if engine == "bing":
    result = js("(function(){var items=document.querySelectorAll('#b_results .b_algo');var res=[];for(var i=0;i<Math.min(items.length,20);i++){var el=items[i];var a=el.querySelector('h2 a');var p=el.querySelector('.b_caption p');res.push({title:a?a.textContent:'',url:a?a.href:'',description:p?p.textContent:''})}return JSON.stringify(res)})()")
elif engine == "google":
    result = js("(function(){var items=document.querySelectorAll('.g');var res=[];for(var i=0;i<Math.min(items.length,20);i++){var el=items[i];var a=el.querySelector('a h3')?el.querySelector('a'):null;var s=el.querySelector('.VwiC3b');res.push({title:a?a.textContent:'',url:a?a.href:'',description:s?s.textContent:''})}return JSON.stringify(res)})()")
elif engine == "baidu":
    result = js("(function(){var items=document.querySelectorAll('.result.c-container');var res=[];for(var i=0;i<Math.min(items.length,20);i++){var el=items[i];var a=el.querySelector('h3 a');var abs=el.querySelector('.content-right_8Zs40,.c-abstract');res.push({title:a?a.textContent:'',url:a?a.href:'',description:abs?abs.textContent:''})}return JSON.stringify(res)})()")
else:
    result = "[]"

print(result)
"""


@mcp.tool()
def list_scripts(url: str) -> str:
    """列出目标页面加载的所有JavaScript脚本文件。参考js-reverse-mcp的脚本分析能力。"""
    try:
        script = _LIST_SCRIPTS_JS.replace("__TARGET_URL__", "'" + url + "'")
        raw = run_bh(script, timeout=30)
        items = json.loads(raw)
        return json.dumps({"count": len(items), "scripts": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def search_scripts(url: str, keyword: str) -> str:
    """在目标页面所有JS脚本中搜索关键词，返回匹配位置和上下文。用于定位签名/加密函数。"""
    try:
        script = _SEARCH_SCRIPTS_JS.replace("__TARGET_URL__", "'" + url + "'").replace("__KEYWORD__", keyword)
        raw = run_bh(script, timeout=60)
        items = json.loads(raw)
        return json.dumps({"keyword": keyword, "matched_scripts": len(items), "results": items}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_script_source(script_url: str) -> str:
    """获取指定JS脚本的源代码。用于分析签名算法、加密逻辑等。"""
    try:
        script = _GET_SCRIPT_SOURCE_JS.replace("__SCRIPT_URL__", script_url)
        raw = run_bh(script, timeout=30)
        return raw
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def export_request_detail(url: str, filter_keyword: str = "") -> str:
    """导出目标页面的完整网络请求详情（headers/body/response）。用于分析API协议。"""
    try:
        script = (_EXPORT_REQUEST_JS
                  .replace("__TARGET_URL__", "'" + url + "'")
                  .replace("__FILTER__", filter_keyword))
        return run_bh(script, timeout=30)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def take_screenshot(url: str = "") -> str:
    """截取当前页面或指定URL的截图，保存到本地。返回文件路径。"""
    try:
        import os
        os.makedirs("E:/skill/screenshots", exist_ok=True)
        ts = str(int(time.time()))
        path = f"E:/skill/screenshots/screenshot_{ts}.png"

        if url:
            script = f"""
import time
from browser_harness.helpers import js
js("window.location.href='{url}'")
time.sleep(6)
capture_screenshot("{path}")
print("{path}")
"""
        else:
            script = f"""
from browser_harness.helpers import js
capture_screenshot("{path}")
print("{path}")
"""
        raw = run_bh(script, timeout=20)
        return json.dumps({"path": raw.strip(), "url": url or "current page"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def web_search(query: str, engine: str = "bing", max_results: int = 10) -> str:
    """
    通用Web搜索引擎，无需API Key。支持Bing/Google/百度。

    Args:
        query: 搜索关键词
        engine: 搜索引擎 (bing/google/baidu)
        max_results: 最大结果数

    Returns:
        JSON数组: [{title, url, description}]
    """
    try:
        script = (_WEB_SEARCH_JS
                  .replace("__QUERY__", query.replace('"', '\\"'))
                  .replace("__ENGINE__", engine))
        raw = run_bh(script, timeout=30)
        items = json.loads(raw)
        return json.dumps({"engine": engine, "query": query, "count": len(items[:max_results]), "items": items[:max_results]}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    logger.info("Unified Search MCP Server starting...")
    mcp.run(transport="stdio")
