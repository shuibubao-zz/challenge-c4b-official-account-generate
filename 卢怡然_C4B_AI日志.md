# C4B AI 日志：用 skill-creator 做一个公众号文章生成技能

> 作者：卢怡然 ｜ 日期：2026-10-06
> 挑战要求：**必须使用 skill-creator** 来创建/迭代技能，且 AI 日志是评审必交项。
> 本文记录真实过程，包括跑不通的地方与改了几次。

---

## 一、起点：任务与硬约束

| 约束 | 来源 | 我的处理 |
|------|------|----------|
| 必须从 starter kit 出发 | CHALLENGE.md 拿来主义原则 | 保留 `C4B/_starter/` 原样，逐文件对照改造 |
| 必须使用 skill-creator | CHALLENGE.md AI-First 原则 | 走完整六步（见第二节） |
| 必须发布一篇真实文章 | Level 3 | **网页版已发布**（真实链接见第五节）；公众号后台发布需本人账号，未完成，如实标注（见 `卢怡然_C4B_文章链接.md`） |
| 评分维度 | 平台 `rubric.json` | 内容质量 25 / 传播设计 20 / 产物完整性 15 / AI 使用质量 20 / 复盘质量 20 |

一个必须先说清楚的偏差：CHALLENGE.md 写的是"文章质量 30% / 技能定制深度 25%"，
而随包的 `rubric.json` 是"内容质量 25 / 传播设计 20 / 产物完整性 15 / AI 20 / 复盘 20"。
**我按 rubric.json 准备**（它是平台机读的评分卡），同时兼顾 CHALLENGE.md 里"新增 ≥2 项能力"的要求。

---

## 二、skill-creator 六步流程实录

### Step 1 — Understanding the Skill with Concrete Examples（问清楚怎么用）

skill-creator 要求先用具体例子界定能力边界，不能直接开写。我向用户提了两个问题（这是真实提问，不是自问自答）：

1. **有没有可发布的公众号？** → 答：没有，如实标注未发布。
   这个答案直接决定了"传播设计 20 分"怎么拿：拿不到真实阅读数据，就转而交付发布 SOP + 数据追踪表。
2. **文章写什么主题？** → 答：公众号排版踩坑指南。
   这个答案决定了技能要先支持什么：技术文必须支持代码块、表格、callout，所以这三项排在最前面。

同时我自己列了 4 条"用户会怎么说"的触发语句，写进了 SKILL.md 的 `description`。

### Step 2 — Planning the Reusable Skill Contents（规划可复用内容）

按 skill-creator 的建议逐项判断该放 scripts / references / assets 哪一类：

| 内容 | 归类 | 理由 |
|------|------|------|
| 转换器、主题、排版、检查器、测试 | `scripts/` | 需要确定性、会反复执行 |
| 限制规则、样式取值、能力语法、排障清单 | `references/` | 让 SKILL.md 保持精简，按需加载 |
| 文章模板 | `assets/` | 直接被复制到输出里用 |

### Step 3 — Initializing the Skill（用官方脚本初始化）

```bash
python <skill-creator>/scripts/init_skill.py wechat-publisher --path C:/Users/卢怡然/Desktop/C4B
```

输出：`✅ Created SKILL.md / scripts/example.py / references/api_reference.md / assets/example_asset.txt`。
随后删掉了三个示例文件——它们只是模板占位，留着会让评审以为交付物是空的。

### Step 4 — Edit the Skill（实现）

按"先做可复用资源，再写 SKILL.md"的顺序：

1. `themes.py` 主题系统 → 2. `typography.py` 中文排版 → 3. `md_lite.py` 零依赖解析
→ 4. `wechat_check.py` 合规检查 → 5. `convert_to_wechat.py` 主流程 → 6. `selftest.py` eval
→ 7. 四份 references + 文章模板 + 样例 → 8. 最后写 SKILL.md（frontmatter 含 `agent_created: true`）

### Step 5 — Packaging（用官方脚本打包 + 校验）

```bash
python <skill-creator>/scripts/package_skill.py C:/Users/卢怡然/Desktop/C4B/wechat-publisher
```

官方脚本会先做校验（frontmatter、命名、结构、描述完整度），通过才打包。
**这一步真的报错了一次**：

```
❌ Validation failed: Description cannot contain angle brackets (< or >)
```

原因是我把 description 写成了 YAML 折叠标量 `description: >`，那个 `>` 被校验器判为尖括号。
改成 `description: |` 后通过（`✅ Skill is valid!`）。
这是"用官方工具"才有价值的地方——自己打包永远不会发现这个约定。
产物留档在 `evidence/官方打包器输出_wechat-publisher.zip`；
交付用的 `卢怡然_C4B_wechat-publisher.skill` 是 SKILL.md 在根的格式（便于直接解包到技能目录）。

### Step 6 — Iterate（按 eval 结果迭代）

`selftest.py` 就是 eval harness。首轮 **5/16**，最终 **20/20**。中间每一轮修的都是真问题，见下。

---

## 三、迭代轮次（eval 驱动的 6 轮修复）

| 轮次 | eval 结果 | 修了什么 | 性质 |
|------|-----------|----------|------|
| 初版 | 5/16 | `re.finditer` 的 Match 对象不能直接解包（写成了 `for a, b in finditer`），导致 11 个用例全崩 | 我的低级 bug |
| 2 轮 | 9/16 | 列表子节点用裸 list 存，导致遍历时 `KeyError: 'type'`；改为把子列表包装成完整 list 节点 | 设计教训：IR 里只保留一种节点类型 |
| 3 轮 | 12/16 | `:::warning` 围栏 markdown 库不认识 → 新增 `convert_callout_fences()` 把它改写成 `> [!WARNING]`；`[!NOTE]` 标记识别不支持多行 → 改成扫描块内所有段落并切分 | **真缺陷**（不跑双引擎对比发现不了） |
| 4 轮 | 14/16 | Python-Markdown 会把相邻两个引用块合并成一个 `<blockquote>`，callout 全部串味 → 改为块内扫描切分 | 真缺陷 |
| 5 轮 | 15/16 | 空引用块被输出成 `quote:plain` 占位；签名里 kind 大小写不一致 | 一致性 |
| 6 轮 | 16/16 | 合规检查把闭合标签也计进统计（h2 数翻倍） | 统计口径 |

2026-10-07 追加 **第 7 轮（公式 + 发布轮）**：eval 从 16 项扩到 **20 项**（新增 4 条公式用例），
全部通过。这一轮的动机、实现与两个新发现见第七节。

### 两个"不跑 eval 就发现不了"的发现

**发现 1：Python-Markdown 会合并相邻引用块。**
同一个 Markdown 文件里写两个 callout，中间只隔一个空行，Python-Markdown 会把它们合并成一个
`<blockquote>`，导致第二个 callout 变成第一个的正文。我原来的代码只检查块内第一段，于是"注意框"消失了。
修法是扫描块内所有段落，遇到 `[!KIND]` 就切分出新的 callout。

**发现 2：`nl2br` 让两条解析路径永远对不齐。**
starter 用了 `nl2br` 扩展，它会把源码里一次换行渲染成两个 `<br>`；
我写的零依赖解析器是一个换行一个 `<br>`。为了让"零依赖降级"这件事可信，
我必须让两条路径产出一致——去掉 `nl2br`，改在渲染时统一转换。
最终两条路径对同一输入的输出 **sha256 完全一致**（`1e506b85cffe6993…`）。

---

## 四、AI 用得好的地方 / 用得不好的地方

### 用得好的

1. **先问再写**。问"有没有公众号"不是走形式——它决定了 20 分维度的策略，
   也让我一开始就放弃"伪造发布截图"这条路。
2. **用断言代替"看着没问题"**。16 条 eval 里最有价值的不是"能跑"，
   而是"两条引擎字节一致"和"检查器能抓到坏 HTML"这两条互相验证的断言。
3. **保留基线做对照**。starter 的原版输出存在 `evidence/baseline_starter_output.html`，
   "我改了什么"因此是可量化的，不是自述。

### 用得不好的（失败记录）

1. **第一版把 `~~( ?P<dbody>.+?)~~` 写错了正则语法**（空格混进了组名），
   语法层面就直接报错，浪费一轮。教训：正则写长表达式时先单独跑一遍再嵌进大正则。
2. **最初想让 `selftest.py` 复用 starter 的 `read_docx`**，
   结果在无 python-docx 环境下直接抛 ImportError 堆栈而不是可操作提示。
   改成"捕获并给出 `pip install python-docx` 的明确提示"，并为此加了一条 eval。
3. **一度想让脚本自动 pip install**（starter 就是这么做的）。
   写到一半停手了：未经允许修改用户环境不是好行为。改成"能降级就降级，不能降级就给提示"。

---

## 五、2026-10-07 追加轮：发布与数学公式

### 6.1 传播设计补完：网页版发布

用户确认后，把 `卢怡然_C4B_output.html` 以静态页方式发布上线：
**https://wechat-article-layout-38529.app.workbuddy.host/**（真实可访问，`site/index.html` 为源）。
公众号后台发布仍需本人账号，`文章链接.md` 里按"是什么/不是什么"如实区分。

### 6.2 补齐数学公式（LaTeX → PNG）

当初"诚实标注没做"的能力，在装好 matplotlib 后补上了。方案与理由：

- **为什么必须是图片**：MathJax/KaTeX 依赖 `<script>`，公众号保存时全剥（文章坑 4）；
  SVG 输出也会消失（坑 5）。PNG + base64 内嵌是唯一活路。
- **为什么用 mathtext**：matplotlib 自带，**不需要本机装 LaTeX**；代价是只支持子集，常见公式够用。
- **实现**：`scripts/math_render.py`（渲染 + 缓存）；`md_lite.py` 的 tokenizer 增加 `$…$` / `$$…$$`，
  渲染成 `<img>`，**缺 matplotlib 时降级为红字等宽文本并写入告警——不假装支持**；
  `convert_to_wechat.py` 在 inline 清洗阶段**跳过 `<code>` 区域**再做公式替换
  （防止命令行 `$PATH` 被误伤），并用占位符延后插回（防止公式 `<img>` 被图片归一化覆盖样式）。
- **eval 扩项**：渲染/降级、双引擎字节一致、代码区 `$` 不误伤、`--math off`，16 → **20 项**。

### 6.3 这一轮抓到的两个真问题

1. **透明底公式图在深色模式会隐形。** 我先按习惯用透明 PNG + 黑字渲染，真渲染出来一看：
   深色背景上几乎看不见。公众号有深色模式，黑字透明图会被吞掉。改为**白底深字**
   （白底在白色正文里无缝，深色模式下也不会消失）。
   教训：**"能渲染出来"和"在目标环境里看得见"是两回事，必须真的看一眼产物。**
2. **自家检查器抓到了自家输出。** 第一次转换后合规自检报 `[错误] 违规 CSS 属性 height`——
   来源是我给公式 `<img>` 写的 `height:auto`。img 只约束 `max-width` 时浏览器本就保持纵横比，
   删掉即可。这正是文章里"把规则固化成检查器"的价值：**写检查器的人第一个救的是自己。**

---

## 七、v2 加固轮（2026-10-07 晚，回应评审意见）

评审给出五条意见：文章无图、7 个坑缺外部依据、自检 20/20 口径不清、发布口径矛盾、
包内垃圾文件。本轮逐条落实，且过程中抓出两个新问题（详见 AAR 失败 6/7）。

### 7.1 P0-1 配图：3 张图，每张都承载真实数据

用 matplotlib（隔离 venv）+ 微软雅黑生成，白底（防公众号深色模式吞图）、dpi=100
（宽约 960px，贴近官方建议的 900px），全部走转换器的 base64 内嵌路径：

| 图 | 内容 | 数据来源 |
|----|------|----------|
| fig1_pipeline.png | 转换流水线，红色回环=合规自检不过就报错 | convert_to_wechat.py 实际执行顺序 |
| fig2_pitfalls.png | 7 坑速查表，右侧列=每条的依据级别 | 本轮查证结论 |
| fig3_evidence.png | 依据分布：官方明文 2 / 由官方推出 1 / 未找到官方出处 4 | 外部依据_官方原文摘录.md |

生成脚本 `evidence/生成文章配图.py` 留档可复跑。过程中修了 3 个渲染问题：
中英文引号嵌套导致的语法错误、微软雅黑缺 ✅/⚠ 字形（会画成方框，全部改文字）、
fig2 副标题与表头重叠。

### 7.2 P0-2 外部依据：先查证，再标注，被抓出一条错的

1. 直接抓取微信官方文档页（urllib → 剥标签 → 逐字摘录），拿到三处 L1 出处：
   新增草稿接口（"此处会去除JS""外部图片url将被过滤""必须少于2万字符，小于1M"）、
   上传永久素材接口（"微信后台将过滤外部的图片链接"、图片格式/大小清单）、
   新增临时素材接口（图片 10M、同页"图片2MB"冲突）。
2. 诚实边界：**坑 1/2/3/6（class/style、h1、div、pre）查不到官方出处**——微信从未公开
   编辑器 HTML 白名单。文章对这 4 条明确标注"未找到官方出处"，不伪装成官方条文；
   坑 7 标注为"由坑 4 推出"。
3. 官方文档内部的 4 处口径冲突（字数、图片大小、格式清单、"2kb vs 1M"笔误）逐条裁定，
   检查器 `wechat_check.py` 的告警文案同步改为官方口径，并按更保守的 2MB 提醒。
4. **抓出自己写错的规则**："单篇不超过 100 张"查无出处（官方社区帖反而说无数量限制，
   但需登录无法二次核验）。已从文章与 references 删除、文章里公开交代勘误，
   并在核验脚本里加回归护栏（该短语不带解释性标记重新出现即报错）。
5. 产物：`evidence/外部依据_官方原文摘录.md`（摘录+冲突裁定+权威性排序+诚实清单）+
   `evidence/外部依据_核验.py`（联网核验 10 条原文 + 回归护栏，实测全绿）。

### 7.3 P1 自检口径：发现留档与真机对不上

查证时发现系统 python **一个第三方库都没装**——直接跑 selftest 是 18/20，
而留档写 20/20。根因：20/20 是用隔离 venv（装了四个库）跑的，留档没写解释器路径。
第一版复测脚本还有两个 bug：把"本机"当依赖齐全来标注、输出只打印最后 3 行。

重写为 `evidence/selftest_双环境口径.py`：**同一解释器跑两遍，唯一变量=四个库是否可见**
（严格对照实验）→ 满依赖 20/20、干净环境 18/20，掉的两项及原因逐条打印。
两份留档 `selftest_20项.txt` / `selftest_18项_零依赖.txt` 均带解释器路径与复现命令。
修改 wechat_check.py 后两环境复跑，仍为 20/20 与 18/20。

### 7.4 P2 发布口径：写死"只有一个渠道"

本地 grep 确认包内从未出现 GitHub Pages 表述，线上链接 HTTP 200。
README 顶部与 `文章链接.md` §一 都加了"发布渠道口径"段：
唯一真实渠道 = WorkBuddy 托管网页版；GitHub Pages 从未启用；公众号从未发布。
v2 完成后重新转换并同步 `site/index.html`，重新部署线上页。

### 7.5 P3 垃圾文件：核过，没有

`find wechat-publisher -type f` 共 17 个文件，无 `__pycache__`/`*.pyc`/`.DS_Store`；
官方打包器输出的 zip 内同样干净（`evidence/审计说明_命名与空文件.md` 有逐文件清单）。

### 7.6 AI 参与度（v2 轮）

约 60%。AI 做了：官方文档抓取与逐字摘录、核验脚本与对照实验设计、配图代码、
文档同步。人做了：决定"查不到出处就如实标注"的口径、确认"100 张"这条按删掉处理、
逐张看过配图效果（发现副标题重叠/字形缺字两处问题）。

---

## 八、时间与证据

| 时间 | 动作 | 产出 |
|------|------|------|
| 20:34 | 读挑战资料、解压 starter（校验 SHA-256 与官方清单一致） | `C4B/_starter/` |
| 20:40 | 用 skill-creator 初始化骨架 | `wechat-publisher/` |
| 20:41–21:00 | 实现 6 个模块 + 4 份 references | `scripts/*.py` |
| 21:00–21:10 | 6 轮 eval 迭代 5/16 → 16/16 | `evidence/selftest_16项.txt` |
| 21:10 | starter 基线 vs 定制版对照、屏蔽依赖跑零依赖路径 | `evidence/baseline_vs_custom.txt` |
| 21:15 | 写文章源文件并转换 | `卢怡然_C4B_output.html`（4125 字，合规通过） |
| 次日 | 用户确认后发布网页版文章页 | **https://wechat-article-layout-38529.app.workbuddy.host/** |
| 次日 | 装环境、写 `math_render.py`、改造 `md_lite.py` / `convert_to_wechat.py`、eval 扩到 20 项 | `scripts/math_render.py`、`evidence/selftest_20项.txt` |
| 次日 | 真渲染验证发现透明底隐患 → 改白底；自家检查器抓到 `height:auto` → 修复后重转换 | `卢怡然_C4B_output.html`（4742 字 / 1 图，合规通过） |
| v2 晚 | 逐字抓取 3 处官方文档、写核验脚本+回归护栏、修正"100 张"错误断言 | `evidence/外部依据_官方原文摘录.md`、`外部依据_核验.py`（全绿） |
| v2 晚 | 生成 3 张配图（修 3 个渲染问题）→ 重写文章（6660 字）→ 重转换 | `images/`、`卢怡然_C4B_output.html`（6660 字 / 4 图，合规通过） |
| v2 晚 | 发现留档 20/20 与真机 18/20 不一致 → 重写为双环境对照实验 → 改检查器后复跑 | `evidence/selftest_双环境口径.py` 及两份留档 |
| v2 晚 | 同步 README / 文章链接 / AAR / AI 日志 / 教学说明 / 拿来说明 → 重打包 → 重新部署 | `.skill`、线上页（6660 字带图版） |

**证据文件**

| 文件 | 内容 |
|------|------|
| `evidence/selftest_16项.txt` | 第一轮 eval 全量输出（16/16，历史） |
| `evidence/selftest_20项.txt` | 满依赖环境 20/20（带解释器路径与复现命令） |
| `evidence/selftest_18项_零依赖.txt` | 零依赖环境 18/20（同上） |
| `evidence/selftest_双环境口径.py` + `_输出.txt` | 同一解释器、唯一变量=依赖可见性的对照实验 |
| `evidence/外部依据_官方原文摘录.md` | 官方原文逐字摘录 + 4 处口径冲突裁定 + 权威性排序 |
| `evidence/外部依据_核验.py` + `_输出.txt` | 10 条原文联网核验 + "100 张"回归护栏（全绿） |
| `evidence/生成文章配图.py` | 3 张配图的生成脚本 |
| `evidence/baseline_vs_custom.txt` | 与 starter 基线的量化对照 + 双引擎 sha256 |
| `evidence/baseline_starter_output.html` | starter 原版输出（未经修改） |
| `evidence/mine_same_input.html` / `mine_zero_dep.html` | 定制版两条路径输出（字节一致） |
| `evidence/article_convert_report.json` | 真实文章的转换与自检报告（6660 字 / 4 图） |
| `evidence/skill安装验证.txt` | 解包副本上独立运行验证 |
| 线上链接 | https://wechat-article-layout-38529.app.workbuddy.host/ |
