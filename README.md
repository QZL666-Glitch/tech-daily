# 公众号内容自动生成系统

每天自动抓取「生物医学工程 / 嵌入式 STM32·ESP32 / 3D 打印 / GitHub·Gitee 开源项目」等方向的最新内容，用大模型润色成「专业但看得懂」的文章，并在结尾自动附加 **AI 解读 + 知识总结 + 小白常见问题 Q&A**，最后生成公众号可直接粘贴的排版。

---

## 一、它能做什么（流程）

```
抓取来源 ──▶ 相关性筛选 ──▶ 去重(历史已发) ──▶ LLM 润色成文
                                                      │
                                      ┌───────────────┴───────────────┐
                                      ▼                                ▼
                              AI 解读 + 知识总结              小白常见问题 Q&A
                              + 事实核查说明                 （6~10 个问答）
                                      │
                                      ▼
                          生成 .md / .html / .txt
                              │
              ┌───────────────┴────────────────┐
              ▼                                 ▼
     手动兜底：复制 HTML 到公众号        （可选）微信 API 自动发布
     编辑器“源代码”模式一键粘贴         需认证企业公众号
```

**内置内容来源：**
- GitHub Search API：按 `stm32 / esp32 / embedded / biomedical / medical-device / 3d-printing / wearable / bioinformatics` 主题抓近期活跃仓库
- Gitee Search API：国内直连，`stm32 / esp32 / 嵌入式 / 3d打印 / 生物医学`
- arXiv API：`physics.med-ph / q-bio.QM / eess.SP / eess.IV`（生物医学工程、医学影像、信号处理）
- 通用 RSS（可自行扩展）；Reddit / Hacker News（大陆需代理，默认关闭）

**防编造设计（针对你的核心要求）：**
- 润色提示词强制「只依据素材写作，禁止补写数据/人名/结论/链接」
- 解读环节要求「合理推断标注（推断），没写清楚的标注『文中未说明』」
- 每篇末尾输出一行 **【事实核查】** 说明哪些有原文依据、哪些是推断/存疑
- 文末附「参考来源」链接，读者可自行溯源

---

## 二、前置准备（先做这 4 件事）

### 1. 注册微信公众号
到 https://mp.weixin.qq.com 注册。

**账号类型决定你能不能全自动发布（务必先看懂）：**

| 账号 | 能否调用发布 API | 说明 |
| --- | --- | --- |
| 个人订阅号（免费） | ❌ 不能 | 2025-07 起微信已回收个人主体的发布接口权限，调接口返回 `48001 api unauthorized` |
| 认证企业订阅号/服务号（蓝V） | ✅ 能 | 需要企业资质 + 300 元/年认证 |
| 个人实名认证（黄V） | ❌ 不能 | 黄V 不是企业认证，不解锁发布接口 |

> **结论**：学生个人注册通常是「个人订阅号」，走 **手动发布**（本系统默认模式，自动生成好文章你复制粘贴即可）。想全自动，需要企业主体认证账号。

### 2. 申请大模型 API Key（以 DeepSeek 为例）
1. 打开 https://platform.deepseek.com ，注册并登录
2. 充值（10 元起步即可，很便宜）
3. 左侧「API Keys」→「创建 API Key」→ 复制 `sk-xxx` 保存好（只显示一次）

> 其他可选：通义千问、智谱 GLM、Kimi 等，只要支持 OpenAI 兼容格式，改 `llm.base_url` + `llm.model` 即可。

### 3.（可选）GitHub Token
GitHub 未认证搜索接口限速较严。去 https://github.com/settings/tokens 生成一个只读 Token（勾 `public_repo` 即可），填进配置可大幅提高稳定性。

### 4. 安装 Python
本项目用 Python 3.10+ 即可（本机已装 3.13）。

---

## 三、本地运行步骤（Windows）

打开 PowerShell，进入项目目录：

```powershell
cd "C:\Users\Administrator\Doubao\chats\2026-11-16\new-chat-1\wechat-tech-daily"
```

**第 1 步：装依赖**

```powershell
python -m pip install -r requirements.txt
```

**第 2 步：填配置**

```powershell
Copy-Item config.example.yaml config.yaml
notepad config.yaml
```

至少改这几项：

```yaml
llm:
  api_key: "sk-你的DeepSeek密钥"     # 必填
```

**第 3 步：先试跑「只抓取不生成」**（验证网络和来源是否正常）

```powershell
python main.py --dry-run
```

**第 4 步：正式跑一轮**

```powershell
python main.py
```

跑完后，文章会生成在 `output\当天日期\` 下，每篇有 3 个文件：
- `.md`：纯文本查看
- `.html`：微信公众号排版（复制粘贴用）
- `.txt`：纯文本

---

## 四、怎么发到公众号（手动模式，个人号）

1. 打开 https://mp.weixin.qq.com → 登录 → 「草稿箱」→「新建图文」
2. 右上角找到编辑器工具栏里的 **「源代码」**（或「HTML」）按钮，切换到源码模式
3. 打开 `output\当天日期\文章名.html`，全选复制，粘贴进去
4. 切回正常编辑模式，自己加个封面图 → 点「发表」

> 每天最多 1 条（订阅号限制），建议每篇只挑最好的 1 篇发。

---

## 五、全自动发布（仅认证企业公众号）

如果你有「认证企业」公众号，可以走 API 全自动：

```yaml
run:
  mode: "publish"            # 改成 publish
wechat:
  enabled: true
  appid: "你的AppID"
  appsecret: "你的AppSecret"
  thumb_image: "C:\\path\\to\\cover.png"   # 封面图本地路径
```

AppID/AppSecret 在「公众平台后台 → 设置与开发 → 基本配置」里。**同时要把调用服务器的出口 IP 加进同页面的「IP 白名单」**，否则报 `40164`。

发布接口调用链（代码里已实现）：`access_token → 上传封面 → draft/add 建草稿 → freepublish/submit 提交发布`。注意这是「发布/发表」，不是「群发通知」，不会给粉丝推消息，但会进公众号历史消息并可被搜一搜收录。

---

## 六、三种定时方案（选一种）

### 方案 A：本地电脑 + Windows 任务计划程序（最省事，但需电脑开着）
1. `Win + R` 输入 `taskschd.msc` 打开任务计划程序
2. 「创建基本任务」→ 名称随便填 → 触发器选「每天」设时间
3. 操作选「启动程序」：
   - 程序：`python` 的完整路径（`python -c "import sys;print(sys.executable)"` 可查到）
   - 参数：`main.py`
   - 起始于：项目目录完整路径

### 方案 B：GitHub Actions（免费、云端、无需电脑常开，推荐）
1. 把本项目推到一个 **私有** GitHub 仓库（私有保护密钥）
2. 仓库 `Settings → Secrets and variables → Actions` 添加：
   - `LLM_API_KEY`（必填）
   - 可选：`GH_TOKEN`、`WECHAT_APPID`、`WECHAT_APPSECRET`、`WECHAT_ENABLED`
3. 已内置 `.github/workflows/daily.yml`，每天北京时间 06:00 自动跑，结果存为 artifact 可下载
4. 想立即试跑：仓库 `Actions → 每日公众号内容生成 → Run workflow`

> 注意：GitHub Actions 里的机器在大陆外，能正常访问 GitHub；但如果你想在 Actions 里发布到微信，需要把 Actions 的出口 IP 加白名单（IP 会变，较麻烦），所以 **Actions 更适合「自动生成」而不是「自动发布」**。

### 方案 C：云服务器 + cron（Linux）
```bash
crontab -e
# 每天 8:00 跑
0 8 * * * cd /path/to/wechat-tech-daily && /usr/bin/python3 main.py >> logs.txt 2>&1
```

---

## 七、目录结构

```
wechat-tech-daily/
├── main.py                 # 主入口
├── scheduler.py            # 本地定时
├── config.example.yaml     # 配置模板（复制成 config.yaml 使用）
├── requirements.txt
├── .github/workflows/daily.yml   # GitHub Actions 定时
├── src/
│   ├── config.py           # 配置加载 + 环境变量覆盖
│   ├── storage.py          # SQLite 去重/历史
│   ├── sources/            # 抓取来源
│   │   ├── github.py  gitee.py  arxiv.py  rss.py  community.py
│   │   └── aggregate.py    # 汇总 + 相关性评分 + 去重
│   ├── llm/                # 大模型
│   │   ├── client.py       # OpenAI 兼容客户端
│   │   ├── prompts.py      # 润色/解读/QA 提示词（可改文案风格）
│   │   └── article.py      # 生成编排
│   └── publish/
│       ├── html.py         # Markdown → 公众号内联样式 HTML
│       ├── wechat.py       # 微信 API（草稿+发布）
│       └── fallback.py     # 手动发布文件落盘
├── output/                 # 生成结果（按日期）
└── data/                   # 历史记录数据库（防重复）
```

---

## 八、想改文案风格 / 内容方向

- **改文章风格、语气、篇幅**：编辑 `src/llm/prompts.py` 里的提示词
- **加/减抓取方向**：编辑 `config.yaml` 的 `sources` 里的 `topics` / `keywords` / `categories`
- **加新来源**：在 `src/sources/` 下新建一个模块，仿照 `github.py` 返回 `SourceItem` 列表，再到 `aggregate.py` 里加一行调用即可

---

## 九、合规与成本提醒

1. **原创性**：本系统是「基于素材重写 + 附来源」，不构成搬运洗稿；但发布前建议人工过一眼，涉及他人原创文章时保留出处或删改重写。
2. **AI 内容标注**：微信对 AI 生成内容有规范，建议在文末保留「AI 解读」声明（本系统已内置免责声明）。
3. **频率**：订阅号每天 1 条，别贪多，质量优先，避免被判定营销号。
4. **成本**：DeepSeek 每篇约 1500 字正文 + 解读，费用大约几分钱，每天几篇一年也就几十元。
