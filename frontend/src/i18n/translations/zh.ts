/**
 * Simplified Chinese translations.
 */
import type { Translations } from "../types.js";

export const zh: Translations = {
  // Existing keys
  thinkingComplete: "{model} 已完成思考",
  thinkingInProgress: "{model} 正在思考...",
  phaseComplete: "阶段 {phase} 完成",

  // App-level
  "app.title": "Quorum",
  "app.subtitle": "多智能体讨论系统",
  "app.loading.backend": "正在启动后端...",
  "app.loading.models": "正在加载模型...",
  "app.loading.validating": "正在校验模型（{current}/{total}）...",
  "app.error.generic": "错误：{error}",
  "app.error.selectModels": "请先选择至少 2 个模型（/models）",
  "app.error.oxfordEven": "Oxford 需要偶数个模型",
  "app.error.methodMin": "{method} 至少需要 {min} 个模型",
  "app.error.exportFormat": "格式：md、text、pdf、json",
  "app.error.validationFailed": "校验失败",
  "app.success.exported": "已导出至 {path}",
  "app.placeholder.selectModels": "输入 /models 选择模型...",
  "app.placeholder.askQuestion": "输入问题...",
  "app.statusBar.commands": "/ 命令 • Tab 顾问 • Ctrl+R 重启 • Ctrl+C 退出",
  "app.statusBar.running": "Esc/Ctrl+R 重启 • Ctrl+C 退出",
  "app.hint.welcome": "输入 /models 选择 AI 模型，或输入 /help 查看命令",

  // Commands
  "cmd.models": "选择 AI 模型",
  "cmd.method": "选择讨论方式",
  "cmd.synthesizer": "选择综合者模式",
  "cmd.status": "查看当前设置",
  "cmd.export": "导出 [md|text|pdf|json]",
  "cmd.clear": "清屏",
  "cmd.help": "查看帮助",
  "cmd.quit": "退出 Quorum",
  "cmd.turns": "设置最大轮次 [数字]",

  // Model Selector
  "selector.model.title": "选择模型",
  "selector.model.instructions": "（Space 切换，Enter 确认）",
  "selector.model.selected": "已选：",
  "selector.model.minimum": "（至少需要 2 个）",
  "selector.model.warning": "请至少选择 2 个模型参与讨论",
  "selector.model.none": "未选择",
  "selector.model.navigation": "↑↓ 移动 • Space 切换 • Enter 确认 • Esc 取消",
  "selector.model.noModels": "无可用模型",
  "selector.model.checkApi": "请检查 .env 中的 API 密钥",

  // Method Selector
  "selector.method.title": "选择讨论方式",
  "selector.method.modelsSelected": "已选 {count} 个模型",
  "selector.method.navigation": "↑↓ 移动 • Enter 选择 • Esc 关闭",
  "selector.method.needsMin": "需要 {min}+ 个模型",
  "selector.method.needsEven": "需要偶数个模型",

  // Synthesizer Selector
  "selector.synthesizer.title": "选择综合者",
  "selector.synthesizer.navigation": "↑↓ 移动 • Enter 选择 • Esc 关闭",

  // Language Selector
  "selector.language.title": "回复语言",
  "selector.language.navigation": "↑↓ 移动 • Enter 选择 • Esc 关闭",
  "cmd.language": "更改回复语言",

  // Method Names and Descriptions
  "method.standard.name": "标准讨论",
  "method.standard.desc": "均衡的共识导向讨论",
  "method.standard.useCase": "通用问题、问题求解",
  "method.standard.requirement": "2+ 个模型",
  "method.oxford.name": "牛津辩论",
  "method.oxford.desc": "正反方团队的形式辩论",
  "method.oxford.useCase": "二选一决策、利弊分析",
  "method.oxford.requirement": "偶数（2、4、6...）",
  "method.advocate.name": "魔鬼代言人",
  "method.advocate.desc": "由一个模型质疑共识",
  "method.advocate.useCase": "压力测试想法、避免群体思维",
  "method.advocate.requirement": "3+ 个模型",
  "method.socratic.name": "苏格拉底对话",
  "method.socratic.desc": "由轮换提问者驱动的问答式对话",
  "method.socratic.useCase": "深度探索、揭示隐含假设",
  "method.socratic.requirement": "2+ 个模型",
  "method.delphi.name": "德尔菲法",
  "method.delphi.desc": "迭代式匿名估计直至收敛",
  "method.delphi.useCase": "预测、估算、预判",
  "method.delphi.requirement": "3+ 个模型",
  "method.brainstorm.name": "头脑风暴",
  "method.brainstorm.desc": "发散→收敛的创意构思（Osborn）",
  "method.brainstorm.useCase": "生成想法、创意方案",
  "method.brainstorm.requirement": "2+ 个模型",
  "method.tradeoff.name": "权衡分析",
  "method.tradeoff.desc": "结构化的多准则决策分析",
  "method.tradeoff.useCase": "比较选项、复杂决策",
  "method.tradeoff.requirement": "2+ 个模型",
  "method.bestFor": "最适合：",

  // Phase label
  "phase.label": "阶段",
  "phase.labelWithNumber": "第 {phase} 阶段",

  // Phase Names - Standard
  "phase.standard.1": "独立作答",
  "phase.standard.2": "结构化批判",
  "phase.standard.3": "讨论",
  "phase.standard.4": "最终立场",
  "phase.standard.5": "综合",

  // Phase Names - Oxford
  "phase.oxford.1": "开场陈述",
  "phase.oxford.2": "反驳",
  "phase.oxford.3": "结案陈词",
  "phase.oxford.4": "判决",

  // Phase Names - Advocate
  "phase.advocate.1": "初始立场",
  "phase.advocate.2": "交叉质询",
  "phase.advocate.3": "裁决",

  // Phase Names - Socratic
  "phase.socratic.1": "初始论点",
  "phase.socratic.2": "苏格拉底式追问",
  "phase.socratic.3": "困惑",

  // Phase Names - Delphi
  "phase.delphi.1": "第 1 轮：独立估算",
  "phase.delphi.2": "第 2 轮：知情修订",
  "phase.delphi.3": "第 3 轮：最终修订",
  "phase.delphi.4": "汇总",

  // Phase Names - Brainstorm
  "phase.brainstorm.1": "发散：疯狂想法",
  "phase.brainstorm.2": "构建：组合与扩展",
  "phase.brainstorm.3": "收敛：筛选与打磨",
  "phase.brainstorm.4": "想法综合",

  // Phase Names - Tradeoff
  "phase.tradeoff.1": "框定：定义备选方案",
  "phase.tradeoff.2": "准则：评估维度",
  "phase.tradeoff.3": "评估：为选项打分",
  "phase.tradeoff.4": "决策",

  // Phase Messages (backend → frontend)
  "phase.standard.1.msg": "{count} 位参与者将独立作答...",
  "phase.standard.2.msg": "所有参与者现在将批判全部回答...",
  "phase.standard.3.msg": "讨论开始，参考全部批判意见...",
  "phase.standard.4.msg": "所有参与者现在将陈述最终立场...",
  "phase.standard.5.msg": "正在综合最终立场...",
  "phase.oxford.1.msg": "开场陈述开始。双方各自陈述立场。",
  "phase.oxford.2.msg": "反驳环节开始。请回应对方的论证。",
  "phase.oxford.3.msg": "结案陈词。原提案方与反对方总结各自立场。",
  "phase.oxford.4.msg": "法官现在将评估这场辩论。",
  "phase.advocate.1.msg": "辩护方陈述初始立场，等待审视。",
  "phase.advocate.2.msg": "魔鬼代言人将逐一交叉质询各辩护方。",
  "phase.advocate.3.msg": "魔鬼代言人宣布裁决。",
  "phase.socratic.1.msg": "一位回答者将就该问题提出初始论点。",
  "phase.socratic.2.msg": "苏格拉底式追问开始。提问者将寻找矛盾之处。",
  "phase.socratic.3.msg": "困惑：论点陈述者反思质询所揭示的内容。",
  "phase.delphi.1.msg": "第 1 轮：所有专家匿名给出独立估算。",
  "phase.delphi.2.msg": "第 2 轮：查看匿名群体估算，如有必要请修订。",
  "phase.delphi.3.msg": "第 3 轮：汇总前的最后一次修订机会。",
  "phase.delphi.4.msg": "正在将最终估算汇总为群体共识。",
  "phase.brainstorm.1.msg": "发散：生成疯狂想法。不做评判——数量优先于质量！",
  "phase.brainstorm.2.msg": "构建：在彼此想法基础上组合与扩展。",
  "phase.brainstorm.3.msg": "收敛：现在可以评估。选出前 3 个想法。",
  "phase.brainstorm.4.msg": "正在综合最终入选的想法。",
  "phase.tradeoff.1.msg": "框定：定义待比较的备选方案。",
  "phase.tradeoff.2.msg": "准则：确立评估维度。",
  "phase.tradeoff.3.msg": "评估：按每个准则为每个备选方案打分（1-10）。",
  "phase.tradeoff.4.msg": "正在结合权衡分析综合建议。",

  // Roles
  "role.for": "正方",
  "role.against": "反方",
  "role.advocate": "魔鬼代言人",
  "role.defender": "辩护方",
  "role.questioner": "提问者",
  "role.respondent": "回答者",
  "role.panelist": "专家",
  "role.ideator": "构思者",
  "role.evaluator": "评估者",

  // Rounds
  "round.opening": "开场陈述",
  "round.rebuttal": "反驳",
  "round.closing": "结案陈述",

  // Messages
  "msg.independentAnswer": "（独立作答）",
  "msg.critique": "（批判）",
  "msg.finalPosition": "（最终立场）",
  "msg.agreements": "一致之处：",
  "msg.disagreements": "分歧之处：",
  "msg.missing": "缺失：",
  "msg.synthesis": "综合",
  "msg.verdict": "裁决",
  "msg.consensus": "共识",
  "msg.participants": "参与者",
  "msg.question": "问：{question}",
  "msg.startingDiscussion": "正在开始讨论...",
  "msg.phaseInProgress": "阶段 {phase}：{name} 进行中...",
  "msg.pausePrompt": "{previousPhase} 已完成。按 Enter 继续到 {nextPhase}...",
  "msg.discussionComplete": "讨论完成",
  "msg.pressEscNewDiscussion": "按 Esc 开始新的讨论",

  // Confidence
  "msg.confidence.high": "高",
  "msg.confidence.medium": "中",
  "msg.confidence.low": "低",
  "msg.confidence.breakdown": "置信度构成：",
  "msg.confidence.panelist": "专家置信度：",

  // Consensus values (for export)
  "consensus.yes": "是",
  "consensus.no": "否",
  "consensus.partial": "部分",

  // Synthesis labels by method
  "synthesis.aporia": "已抵达困惑",
  "synthesis.decision": "决策",
  "synthesis.convergence": "收敛",
  "synthesis.selectedIdeas": "入选想法",
  "synthesis.agreement": "一致",
  "synthesis.consensus": "共识",
  "synthesis.openQuestions": "未解问题",
  "synthesis.unresolvedQuestions": "未决问题",
  "synthesis.keyContentions": "关键争议",
  "synthesis.outlierPerspectives": "异见视角",
  "synthesis.alternativeDirections": "替代方向",
  "synthesis.keyTradeoffs": "关键权衡",
  "synthesis.notableDifferences": "显著差异",
  "synthesis.reflection": "反思",
  "synthesis.ruling": "裁定",
  "synthesis.adjudication": "裁决",
  "synthesis.aggregatedEstimate": "汇总估算",
  "synthesis.finalIdeas": "最终想法",
  "synthesis.recommendation": "建议",
  "synthesis.synthesisLabel": "综合",
  "synthesis.reflected": "已反思",
  "synthesis.adjudicated": "已裁定",
  "synthesis.synthesized": "已综合",
  "synthesis.ruledBy": "（由 {model} 裁定）",
  "synthesis.by.synthesized": "（由 {model} 综合）",
  "synthesis.by.reflected": "（由 {model} 反思）",
  "synthesis.by.adjudicated": "（由 {model} 裁定）",

  // Synthesis result markers
  "synthesis.result.for": "✓ 支持方",
  "synthesis.result.against": "✗ 反对方",
  "synthesis.result.partial": "◐ 部分达成",

  // Synthesizer Modes
  "synth.first.name": "首个",
  "synth.first.desc": "由首个选中的模型进行综合",
  "synth.random.name": "随机",
  "synth.random.desc": "每次随机选择模型",
  "synth.rotate.name": "轮换",
  "synth.rotate.desc": "在模型之间轮换",

  // Help
  "help.title": "Quorum 帮助",
  "help.commands": "命令：",
  "help.keyboard": "键盘：",
  "help.key.esc": "关闭浮层 / 返回输入",
  "help.key.ctrlC": "取消正在进行的讨论",
  "help.key.arrows": "在选择器中移动",
  "help.key.enter": "提交 / 选择",
  "help.close": "按 Esc 关闭",

  // Team Preview
  "team.title": "团队分配",
  "team.selectRole": "选择 {role}",
  "team.chooseAdvocate": "选择由哪个模型来质疑其他模型：",
  "team.chooseRespondent": "选择由哪个模型来陈述论点：",
  "team.start": "[Enter] 开始",
  "team.swap": "[S] 交换队伍",
  "team.navigation": "↑↓ 移动 • Enter 选择/开始 • Esc 取消",
  "team.navigationOxford": "← → 切换 • Enter 选择 • S 交换 • Esc 取消",
  "team.forTeam": "正方",
  "team.againstTeam": "反方",
  "team.defenders": "辩护方",

  // Export
  "export.title": "导出讨论（{format}）",
  "export.loading": "正在加载讨论...",
  "export.noDiscussions": "未找到讨论",
  "export.noDiscussionsDir": "{dir} 中未找到讨论报告",
  "export.selectPrompt": "选择要导出的讨论：",
  "export.navigation": "↑↓ 移动  Enter 导出  Esc 取消",
  "export.close": "按 Esc 关闭",

  // Export Document (PDF/Markdown)
  "export.doc.title": "Quorum 讨论导出",
  "export.doc.dateLabel": "日期：",
  "export.doc.methodLabel": "讨论方式：",
  "export.doc.modelsLabel": "模型：",
  "export.doc.questionHeader": "问题",
  "export.doc.discussionHeader": "讨论",
  "export.doc.phaseLabel": "阶段",
  "export.doc.critiqueLabel": "批判",
  "export.doc.finalPositionLabel": "最终立场",
  "export.doc.agreementsLabel": "一致之处：",
  "export.doc.disagreementsLabel": "分歧之处：",
  "export.doc.missingLabel": "缺失：",
  "export.doc.confidenceLabel": "置信度：",
  "export.doc.footer": "导出自 [Quorum](https://github.com/Detrol/quorum-cli)",

  // Method Terminology - Result Labels
  "terminology.result.standard": "结果",
  "terminology.result.oxford": "判决",
  "terminology.result.advocate": "裁决",
  "terminology.result.socratic": "困惑",
  "terminology.result.delphi": "汇总",
  "terminology.result.brainstorm": "入选想法",
  "terminology.result.tradeoff": "决策",

  // Method Terminology - Synthesis Labels
  "terminology.synthesis.standard": "综合",
  "terminology.synthesis.oxford": "裁决",
  "terminology.synthesis.advocate": "裁定",
  "terminology.synthesis.socratic": "反思",
  "terminology.synthesis.delphi": "汇总估算",
  "terminology.synthesis.brainstorm": "最终想法",
  "terminology.synthesis.tradeoff": "建议",

  // Method Terminology - Differences Labels
  "terminology.differences.standard": "显著差异",
  "terminology.differences.oxford": "关键争议",
  "terminology.differences.advocate": "未决问题",
  "terminology.differences.socratic": "未解问题",
  "terminology.differences.delphi": "异见视角",
  "terminology.differences.brainstorm": "替代方向",
  "terminology.differences.tradeoff": "关键权衡",

  // Method Terminology - By Labels
  "terminology.by.standard": "综合者",
  "terminology.by.oxford": "裁决者",
  "terminology.by.advocate": "裁定者",
  "terminology.by.socratic": "反思者",
  "terminology.by.delphi": "汇总者",
  "terminology.by.brainstorm": "汇编者",
  "terminology.by.tradeoff": "分析者",

  // Method Terminology - Consensus Labels
  "terminology.consensus.standard": "共识",
  "terminology.consensus.oxford": "决策",
  "terminology.consensus.advocate": "裁决",
  "terminology.consensus.socratic": "已抵达困惑",
  "terminology.consensus.delphi": "收敛",
  "terminology.consensus.brainstorm": "已选想法",
  "terminology.consensus.tradeoff": "一致",

  // Method Advisor
  "advisor.title": "讨论方式顾问",
  "advisor.prompt": "你的问题是？",
  "advisor.analyzing": "正在由 {model} 分析...",
  "advisor.recommended": "推荐：",
  "advisor.navigation": "↑↓ 移动 • Enter 选择 • Backspace 返回 • Esc 取消",
  "advisor.analyzedBy": "由 {model} 分析",
  "advisor.error": "分析失败",
  "advisor.inputHint": "Enter 分析 • Esc 取消",

  // Status
  "status.title": "当前设置",
  "status.models": "模型：",
  "status.method": "讨论方式：",
  "status.synthesizer": "综合者：",
  "status.maxTurns": "最大轮次：",
  "status.default": "默认",
  "status.none": "未选择",

  // Header
  "header.quickCommands": "快捷命令",
  "header.cmdModels": "/models - 选择 AI 模型",
  "header.cmdMethod": "/method - 更改讨论方式",
  "header.cmdExport": "/export - 导出 [md|text|pdf]",
  "header.cmdHelp": "/help - 全部命令",

  // Command Palette
  "palette.title": "命令",
  "palette.hint": "（↑↓ 移动，Enter 执行，Tab 填充，Esc 关闭）",
  "palette.noMatches": "无匹配命令",

  // Discussion method titles
  "discussion.standard": "标准讨论",
  "discussion.oxford": "牛津辩论",
  "discussion.advocate": "魔鬼代言人",
  "discussion.socratic": "苏格拉底对话",
  "discussion.delphi": "德尔菲共识",
  "discussion.brainstorm": "头脑风暴",
  "discussion.tradeoff": "权衡分析",
  "discussion.default": "讨论",
};
