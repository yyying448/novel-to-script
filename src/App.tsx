import { useState, useCallback, useEffect, useRef } from "react"
import type { Provider, Chapter, SSEEvent, ScriptResult, ModelResult } from "./types"
import * as api from "./lib/api"
import ConfigPanel from "./components/ConfigPanel"
import InputPanel from "./components/InputPanel"
import ConvertPanel from "./components/ConvertPanel"
import { StrategyView, VisualView, CharactersView, EpisodesView, CompareView, RevisePanel, YamlView } from "./components/Views"

type Tab = "config" | "input" | "convert" | "strategy" | "visual" | "characters" | "episodes" | "compare" | "revise" | "yaml"

export default function App() {
  const [tab, setTab] = useState<Tab>("config")
  const [providers, setProviders] = useState<Provider[]>([])
  const [apiKey, setApiKey] = useState("")
  const [provider, setProvider] = useState("deepseek")
  const [model, setModel] = useState("")
  const [customUrl, setCustomUrl] = useState("")
  const [novelText, setNovelText] = useState("")
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [chapterMap, setChapterMap] = useState<Record<string, string>>({})
  const [epMinutes, setEpMinutes] = useState(0)
  const [converting, setConverting] = useState(false)
  const [revising, setRevising] = useState(false)
  const [lanes, setLanes] = useState<any[]>([])
  const [scriptResult, setScriptResult] = useState<ScriptResult>({})
  const [allResults, setAllResults] = useState<ModelResult[]>([])
  const [activeModelIdx, setActiveModelIdx] = useState(0)
  const [strategyReport, setStrategyReport] = useState("")
  const [compareResults, setCompareResults] = useState<any[]>([])
  const [toast, setToast] = useState("")
  const [cmpKeyB, setCmpKeyB] = useState(""); const [cmpKeyC, setCmpKeyC] = useState("")
  const [cmpModelB, setCmpModelB] = useState(""); const [cmpModelC, setCmpModelC] = useState("")
  const [cmpProvB, setCmpProvB] = useState("openai"); const [cmpProvC, setCmpProvC] = useState("openai")
  const [editedChapterMap, setEditedChapterMap] = useState<Record<string,string>>({})
  const [revChapter, setRevChapter] = useState("")
  const [revFeedback, setRevFeedback] = useState("")

  useEffect(() => { api.fetchProviders().then(setProviders) }, [])
  useEffect(() => { const t = setTimeout(() => toast && setToast(""), 3000); return () => clearTimeout(t) }, [toast])
  // 场景加载后自动设置第一个章节为修改目标
  useEffect(() => {
    const chs = [...new Set((scriptResult.scenes||[]).map(s=>s.chapter).filter(Boolean))]
    if (chs.length && !revChapter) setRevChapter(chs[0])
  }, [scriptResult.scenes])

  const apiParams = (extra: any = {}) => ({ text: novelText, api_key: apiKey, provider, model: model || undefined, base_url: customUrl || undefined, ...extra })
  const showToast = (m: string) => setToast(m)
  const download = (content: string, filename: string, type = "text/plain") => {
    const b = new Blob([content], { type })
    const u = URL.createObjectURL(b)
    const a = document.createElement("a"); a.href = u; a.download = filename; a.click()
    URL.revokeObjectURL(u)
  }
  const downloadWord = () => {
    const scenes = scriptResult.scenes || []
    let html = `<html><head><meta charset="utf-8"><style>body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;max-width:800px;margin:40px auto}h1{text-align:center}h2{color:#333;border-bottom:2px solid #000;padding-bottom:4px}h3{margin-top:20px}.scene{margin:16px 0;padding:12px;background:#f9f9f9;border-left:3px solid #333}.dialogue{margin:8px 0 8px 20px}.speaker{font-weight:bold}.tone{color:#666;font-size:13px}</style></head><body><h1>剧本</h1>`
    const groups: Record<string, any[]> = {}; scenes.forEach(s => { const c = s.chapter || "?"; if (!groups[c]) groups[c] = []; groups[c].push(s) })
    for (const [ch, chs] of Object.entries(groups)) {
      html += `<h2>${ch}</h2>`
      chs.forEach(s => {
        html += `<div class="scene"><h3>场景 ${s.scene_id} · ${s.location||""}</h3><p>${s.summary||""}</p>`
        if (s.characters_present?.length) html += `<p>出场：${s.characters_present.map((c:any) => c.name).join("、")}</p>`
        ;(s.dialogues||[]).forEach((d: any) => { html += `<div class="dialogue"><p class="speaker">${d.speaker}</p>`; (d.lines||[]).forEach((l: string) => { html += `<p>${l}</p>` }); if (d.tone||d.action) html += `<p class="tone">${d.tone||""} ${d.action||""}</p>`; html += `</div>` })
        if (s.scene_notes) html += `<p style="color:#888">📝 ${s.scene_notes}</p>`
        html += `</div>`
      })
    }
    html += `</body></html>`
    download(html, "script.doc", "application/msword")
  }
  const downloadCharactersWord = () => {
    const chars = scriptResult.characters || []
    let html = `<html><head><meta charset="utf-8"><style>body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;line-height:2;max-width:800px;margin:40px auto}h1{text-align:center}h2{color:#333;border-bottom:2px solid #000;padding-bottom:4px}.char{margin:20px 0;padding:16px;background:#f9f9f9}p{margin:4px 0}</style></head><body><h1>角色档案</h1>`
    chars.forEach((c: any) => {
      html += `<div class="char"><h2>${c.role==="主角"?"⭐":""} ${c.name}（${c.role}）</h2>`
      html += `<p>出场：${c.chapters_count||0}章 · ${c.scene_count||0}场景 · ${c.dialogue_count||0}句台词 · 首次：${c.first_chapter||"?"}</p>`
      if(c.personality) html += `<p><b>性格：</b>${c.personality}</p>`
      if(c.motivation) html += `<p><b>动机：</b>${c.motivation}</p>`
      if(c.speech_style) html += `<p><b>说话风格：</b>${c.speech_style}</p>`
      if(c.identity) html += `<p><b>身份：</b>${c.identity}</p>`
      if(c.appearance) html += `<p><b>外貌：</b>${c.appearance}</p>`
      html += `</div>`
    })
    html += `</body></html>`
    download(html, "characters.doc", "application/msword")
  }
  const downloadEpisodesWord = () => {
    const eps = scriptResult.episodes || []
    let html = `<html><head><meta charset="utf-8"><style>body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.8;max-width:800px;margin:40px auto}h1{text-align:center}h2{border-bottom:2px solid #000;padding-bottom:4px}.scene{margin:8px 0;padding:8px;border-left:3px solid #ccc}p{margin:3px 0}</style></head><body><h1>分集大纲</h1>`
    eps.forEach((ep: any) => {
      html += `<h2>${ep.title}（${ep.scene_count}场 · ⏱${ep.estimated_duration}分）</h2><p>${ep.summary}</p>`
      ;(ep.scenes||[]).forEach((s: any) => { html += `<div class="scene"><p><b>场景${s.scene_id}</b> · ${s.location||""}</p><p>${s.summary||""}</p></div>` })
    })
    html += `</body></html>`
    download(html, "episodes.doc", "application/msword")
  }

  const handleSaveKey = async () => {
    if (!apiKey) return showToast("请输入 API Key")
    const r = await api.validateKey(apiKey, provider, customUrl)
    showToast(r.success ? `✅ ${r.message}` : `❌ ${r.message}`)
  }

  const handleFile = async (e: any) => {
    const files = e.target?.files || e.dataTransfer?.files
    const f = files?.[0]; if (!f) return
    const r = await api.parseFile(f)
    if (r.success) { setNovelText(r.text); showToast(`✅ ${r.filename} ${r.char_count}字`) }
    else showToast(r.error)
  }

  const handlePreview = async () => {
    if (!novelText) return showToast("请先输入小说")
    const r = await api.previewChapters(apiParams())
    if (r.success) { setChapters(r.chapters); setChapterMap(r.chapter_map || {}); setTab("convert") }
    else showToast(r.error)
  }

  const activeModelIdxRef = useRef(activeModelIdx)
  activeModelIdxRef.current = activeModelIdx

  const handleSSE = useCallback((e: SSEEvent) => {
    switch (e.type) {
      case "chapters": if (e.data?.length) { setChapters(e.data); if (e.chapter_map) setChapterMap(e.chapter_map) } break
      case "strategy": if (e.report) { setStrategyReport(e.report); setTab("strategy") } break
      case "progress": {
        const i = e.label === "模型 B" ? 1 : e.label === "模型 C" ? 2 : 0
        setLanes(p => { const n = [...p]; if (!n[i]) n[i] = { label: e.label || "模型 A", current: 0, total: e.total || 1, status: "", percent: 0, done: false }; n[i] = { ...n[i], current: e.current || 0, total: e.total || 1, status: e.status || "", percent: e.percent || 0 }; return n })
        break
      }
      case "partial": {
        const i = e.label === "模型 B" ? 1 : e.label === "模型 C" ? 2 : 0
        const cur = activeModelIdxRef.current
        if (e.scenes) {
          setAllResults(p => { const n = [...p]; n[i] = { ...n[i], label: e.label || "模型 A", scenes: e.scenes || [], characters: e.characters || [], character_count: (e.characters || []).length, episodes: [], episode_count: 0, runtime: {} }; return n })
          if (i === cur || (i === 0 && cur === 0)) setScriptResult({ scenes: e.scenes, characters: e.characters })
        }
        break
      }
      case "model_done":
        setLanes(p => { const n = [...p]; const i = e.idx || 0; n[i] = { ...n[i], done: true, error: e.error }; return n })
        if (e.scenes) {
          setAllResults(p => { const n = [...p]; n[e.idx || 0] = { label: e.label || "", scenes: e.scenes || [], characters: e.characters || [], episodes: e.episodes || [], runtime: e.runtime || {}, character_count: e.character_count || 0, episode_count: e.episode_count || 0, error: e.error }; return n })
        }
        break
      case "compare": if (e.results) setCompareResults(e.results); break
      case "done":
        if (e.result) setScriptResult(e.result)
        if (e.all_results) setAllResults(e.all_results)
        if (e.strategy_report) setStrategyReport(e.strategy_report)
        setConverting(false)
        break
      case "error": showToast("❌ " + e.message); setConverting(false); break
    }
  }, [])

  const handleConvert = () => {
    // 合并章节编辑到全文
    let text = novelText
    for (const [title, content] of Object.entries(editedChapterMap)) {
      const oldContent = chapterMap[title]
      if (oldContent && text.includes(oldContent)) {
        text = text.replace(oldContent, content)
      }
    }
    setConverting(true); setAllResults([]); setScriptResult({}); setStrategyReport(""); setCompareResults([])
    setLanes([{ label: "模型 A", current: 0, total: chapters.length || 1, status: "等待中...", percent: 0, done: false }])
    api.convertNovel({
      ...apiParams({ text }), episode_minutes: epMinutes,
      compare_keys: JSON.stringify([cmpKeyB, cmpKeyC].filter(Boolean)),
      compare_models: JSON.stringify([cmpModelB, cmpModelC].filter(Boolean)),
      compare_providers: JSON.stringify([cmpProvB, cmpProvC].filter(Boolean)),
    } as any, handleSSE, () => { setConverting(false); showToast("✅ 完成") }, (err) => { setConverting(false); showToast("❌ " + err) })
  }

  const handleRevise = async () => {
    if (!revFeedback) return showToast("请输入修改意见")
    if (!revChapter) return showToast("请选择目标章节")
    const allScenes = scriptResult.scenes || []
    const chapterScenes = allScenes.filter(s => s.chapter === revChapter)
    if (!chapterScenes.length) return showToast("该章节暂无剧本数据，请先完成转换")
    const chapterText = chapterMap[revChapter]
    if (!chapterText) return showToast("未找到该章节原文，请重新预览")
    const existingYaml = yamlDump({ scenes: chapterScenes })
    setRevising(true)
    showToast("⏳ 正在修改 " + revChapter + "...")
    try {
      const r = await api.reviseScript({ ...apiParams(), chapter_text: chapterText, existing_yaml: existingYaml, feedback: revFeedback, chapter_title: revChapter })
      if (r.success && r.result?.scenes?.length) {
        const other = allScenes.filter(s => s.chapter !== revChapter)
        const newScenes = r.result.scenes
        const merged = [...other, ...newScenes].sort((a: any, b: any) => (a.scene_id || 0) - (b.scene_id || 0))
        merged.forEach((s: any, i: number) => { s.scene_id = i + 1 })
        // 重新计算角色
        const chars = recomputeCharacters(merged)
        const newResult = { ...scriptResult, scenes: merged, characters: chars, character_count: chars.length, episodes: [], episode_count: 0 }
        setScriptResult(newResult)
        // 同步更新 allResults
        setAllResults(prev => {
          const n = [...prev]
          const idx = activeModelIdxRef.current
          if (n[idx]) n[idx] = { ...n[idx], scenes: merged, characters: chars, character_count: chars.length, episodes: [], episode_count: 0 }
          return n
        })
        setTab("visual")
        showToast("✅ " + revChapter + " 修改成功（" + newScenes.length + "场）角色已同步，分集需重新转换")
        setRevFeedback("")
      } else {
        showToast("❌ " + (r.error || "修改失败：未返回有效剧本"))
      }
    } catch (e: any) { showToast("❌ " + (e.message || "修改异常")) }
    finally { setRevising(false) }
  }

  const viewModel = (idxOrLabel: any) => {
    if (typeof idxOrLabel === "number") {
      setActiveModelIdx(idxOrLabel)
      const r = allResults[idxOrLabel]
      if (r) setScriptResult({ scenes: r.scenes, characters: r.characters, episodes: r.episodes, runtime: r.runtime as any })
    } else if (typeof idxOrLabel === "string") {
      const r = allResults.find((x: any) => x && x.label === idxOrLabel)
      if (r) {
        setActiveModelIdx(allResults.indexOf(r))
        setScriptResult({ scenes: r.scenes || [], characters: r.characters || [], episodes: r.episodes || [], runtime: r.runtime as any || {} })
        setTab("visual")
        showToast("📄 已切换至 " + idxOrLabel)
      } else {
        showToast("⚠️ 数据未就绪，请等待所有模型完成")
      }
    }
  }

  const nav = (t: Tab, icon: string, label: string) => (
    <button onClick={() => setTab(t)}
      className={`w-full text-left px-5 py-3 text-sm flex items-center gap-3 rounded-full transition-all duration-200
        ${tab === t
          ? "bg-black text-white font-semibold shadow-sm"
          : "text-gray-400 hover:text-black hover:bg-gray-100"
        }`}
    >{icon} {label}</button>
  )

  return (
    <div className="flex h-screen bg-[#fafafa]">
      <aside className="w-60 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col p-4 overflow-y-auto">
        <h1 className="text-base font-bold text-black px-3 pb-6 pt-1 tracking-tight">Novel → Script</h1>
        <nav className="flex flex-col gap-1.5 flex-1">
          {nav("config", "⚙️", "配置")}{nav("input", "📁", "输入")}{nav("convert", "🚀", "转换")}
          <div className="border-t border-gray-200 my-3" />
          {nav("strategy", "📋", "策略")}{nav("visual", "🎬", "剧本")}{nav("characters", "👥", "角色")}{nav("episodes", "📺", "分集")}{nav("compare", "🔬", "对比")}{nav("revise", "✏️", "修改")}{nav("yaml", "📄", "YAML")}
        </nav>
        <div className="text-[10px] text-gray-400 px-3 pt-4 border-t border-gray-100">Script Engine v3</div>
      </aside>
      {toast && <div className="fixed top-4 right-4 bg-black text-white px-6 py-3 rounded-full text-sm font-medium z-[9999] shadow-2xl animate-pulse">{toast}</div>}
      <main className="flex-1 overflow-y-auto p-8">
        {(scriptResult.scenes?.length ?? 0) > 0 && (
          <div className="flex items-center gap-2 mb-5 flex-wrap">
            <span className="text-xs text-gray-400 mr-2">下载：</span>
            <button onClick={downloadWord} className="px-3 py-1 text-xs bg-black text-white rounded-full hover:bg-gray-800">Word</button>
            <button onClick={() => download(yamlDump(scriptResult), "script.yaml")} className="px-3 py-1 text-xs border border-gray-300 rounded-full text-gray-500 hover:bg-gray-100">YAML</button>
            <button onClick={() => download(JSON.stringify(scriptResult.scenes, null, 2), "scenes.json")} className="px-3 py-1 text-xs border border-gray-300 rounded-full text-gray-500 hover:bg-gray-100">JSON</button>
            {strategyReport && <button onClick={() => download(strategyReport, "strategy.md")} className="px-3 py-1 text-xs border border-gray-300 rounded-full text-gray-500 hover:bg-gray-100">策略 .md</button>}
            {(scriptResult.characters?.length ?? 0) > 0 && <button onClick={downloadCharactersWord} className="px-3 py-1 text-xs border border-gray-300 rounded-full text-gray-500 hover:bg-gray-100">角色 Word</button>}
            {(scriptResult.episodes?.length ?? 0) > 0 && <button onClick={downloadEpisodesWord} className="px-3 py-1 text-xs border border-gray-300 rounded-full text-gray-500 hover:bg-gray-100">分集 Word</button>}
          </div>
        )}
        {tab === "config" && <ConfigPanel {...{ providers, apiKey, setApiKey, provider, setProvider, model, setModel, customUrl, setCustomUrl, handleSaveKey, showToast, cmpKeyB, setCmpKeyB, cmpModelB, setCmpModelB, cmpProvB, setCmpProvB, cmpKeyC, setCmpKeyC, cmpModelC, setCmpModelC, cmpProvC, setCmpProvC }} />}
        {tab === "input" && <InputPanel {...{ novelText, setNovelText, handleFile, handlePreview }} />}
        {tab === "convert" && <ConvertPanel {...{ chapters, lanes, converting, handleConvert, epMinutes, setEpMinutes, allResults, activeModelIdx, viewModel, chapterMap, setNovelText, novelText, editedChapterMap, setEditedChapterMap, apiKey, provider, model, customUrl, setRevChapter }} />}
        {tab === "strategy" && <StrategyView report={strategyReport} />}
        {tab === "visual" && <VisualView result={scriptResult} />}
        {tab === "characters" && <CharactersView characters={scriptResult.characters||[]} />}
        {tab === "episodes" && <EpisodesView episodes={scriptResult.episodes||[]} epMinutes={epMinutes} />}
        {tab === "compare" && <CompareView results={compareResults} viewModel={viewModel} />}
        {tab === "revise" && <RevisePanel {...{ scriptResult, chapterMap, revChapter, setRevChapter, revFeedback, setRevFeedback, handleRevise, revising }} />}
        {tab === "yaml" && <YamlView result={scriptResult} runtime={scriptResult.runtime} sceneCount={scriptResult.scenes?.length || 0} charCount={scriptResult.characters?.length || 0} epCount={scriptResult.episodes?.length || 0} />}
      </main>
    </div>
  )
}

function recomputeCharacters(scenes: any[]) {
  const map: Record<string, any> = {}
  scenes.forEach((s: any) => {
    (s.characters_present || []).forEach((c: any) => {
      if (!c || !c.name) return
      if (!map[c.name]) map[c.name] = { name: c.name, role: c.role || "配角", chapters: [], scene_count: 0, dialogue_count: 0, personality: "", speech_style: "", identity: "", motivation: "", appearance: "", relationships: {}, first_chapter: s.chapter || "?", chapters_count: 0 }
      const p = map[c.name]
      if (c.role === "主角") p.role = "主角"
      if (!p.chapters.includes(s.chapter)) p.chapters.push(s.chapter)
      p.scene_count++
      p.dialogue_count += (s.dialogues || []).filter((d: any) => d && d.speaker === c.name).length
    })
  })
  const result = Object.values(map)
  result.forEach((c: any) => { c.chapters_count = c.chapters.length })
  result.sort((a: any, b: any) => { const o: Record<string, number> = { "主角": 0, "重要配角": 1 }; return (o[a.role] ?? 2) - (o[b.role] ?? 2) || b.scene_count - a.scene_count })
  return result
}

function yamlDump(o: any, d = 0): string {
  const p = "  ".repeat(d)
  if (o === null || o === undefined) return "null"
  if (typeof o === "string") return (o.includes(":") || o.includes("#") || o.includes("'")) ? `"${o}"` : o
  if (typeof o === "number" || typeof o === "boolean") return String(o)
  if (Array.isArray(o)) { if (o.length === 0) return "[]"; let s = ""; for (const i of o) { if (typeof i === "object" && i !== null) { s += `${p}- `; const n = yamlDump(i, d + 1).trimStart(); s += n.startsWith("- ") ? `\n${n}` : `${n}\n` } else s += `${p}- ${yamlDump(i)}\n` } return s }
  let s = ""; for (const [k, v] of Object.entries(o)) { if (v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0)) s += `${p}${k}: []\n`; else if (Array.isArray(v) && v.length > 0 && typeof v[0] !== "object") s += `${p}${k}: [${v.map((x: any) => yamlDump(x)).join(", ")}]\n`; else if (typeof v === "object" && !Array.isArray(v)) s += `${p}${k}:\n${yamlDump(v, d + 1)}`; else if (Array.isArray(v)) s += `${p}${k}:\n${yamlDump(v, d + 1)}`; else s += `${p}${k}: ${yamlDump(v)}\n` } return s
}
