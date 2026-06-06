import { useState } from "react"
import type { Chapter } from "../types"

export default function ConvertPanel(p: any) {
  const [editing, setEditing] = useState<string | null>(null)
  const [editText, setEditText] = useState("")
  const [aiResult, setAiResult] = useState("")
  const [aiLoading, setAiLoading] = useState(false)
  const colors = ["bg-black","bg-gray-500","bg-gray-300"]

  const openEdit = (ch: Chapter) => {
    setEditing(ch.title)
    setEditText(p.chapterMap?.[ch.title] || "")
    setAiResult("")
  }

  const handleAiEdit = async (mode: "rewrite" | "expand") => {
    const sel = window.getSelection()?.toString()?.trim()
    const text = sel || editText
    if (!text) return
    const instruction = mode === "expand"
      ? `请扩写以下内容，增加细节描写和人物心理活动，使内容更加丰满（保持原文风格）`
      : `请改写以下内容，优化语言表达，使文字更加流畅生动（保持原意不变）`

    setAiLoading(true)
    try {
      const r = await fetch("/api/ai-edit", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ chapter_text: text, feedback: instruction, api_key: p.apiKey, provider: p.provider, base_url: p.customUrl || null, model: p.model || null })
      })
      const d = await r.json()
      if (d.success) setAiResult(d.text)
      else setAiResult("❌ " + (d.error || "失败"))
    } catch (e: any) { setAiResult("❌ " + e.message) }
    finally { setAiLoading(false) }
  }

  const applyAiResult = () => {
    if (!aiResult) return
    const sel = window.getSelection()
    if (sel && sel.toString().trim()) {
      const start = (document.getElementById("chapter-editor") as HTMLTextAreaElement)?.selectionStart || 0
      const end = (document.getElementById("chapter-editor") as HTMLTextAreaElement)?.selectionEnd || 0
      const before = editText.slice(0, start)
      const after = editText.slice(end)
      setEditText(before + aiResult + after)
    } else {
      setEditText(aiResult)
    }
    setAiResult("")
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-5 shadow-sm">
      <h2 className="text-base font-bold text-black mb-5">转换</h2>
      {p.chapters.length > 0 && (
        <div className="mb-5">
          <p className="text-sm text-gray-500 mb-3 font-medium">识别到 {p.chapters.length} 个章节</p>
          <div className="flex flex-wrap gap-2">
            {p.chapters.map((ch: Chapter, i: number) => (
              <span key={i} onClick={() => openEdit(ch)}
                className="px-3 py-1.5 bg-gray-100 border border-gray-200 rounded-full text-xs text-gray-700 cursor-pointer hover:bg-gray-200 hover:border-gray-400 transition-colors">
                {ch.title}<span className="text-gray-400 ml-1">{ch.char_count}字</span>
              </span>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-5">
            <label className="text-sm text-gray-500 font-medium">单集时长</label>
            <input type="number" value={p.epMinutes} onChange={e=>p.setEpMinutes(Number(e.target.value)||0)} min={0} max={180}
              className="w-20 px-3 py-1.5 bg-white border border-gray-300 rounded-full text-sm text-black text-center outline-none focus:border-black/40"/>
            <span className="text-xs text-gray-400">分钟（0=不分集）</span>
            <button onClick={p.handleConvert} disabled={p.converting}
              className="ml-auto px-6 py-2.5 bg-black text-white rounded-full text-sm font-semibold hover:bg-gray-800 disabled:opacity-30 transition-all">{p.converting?"转换中...":"开始转换"}</button>
          </div>
        </div>
      )}
      {p.lanes.length > 0 && (
        <div className="space-y-3">
          {p.lanes.map((l:any,i:number)=>(
            <div key={i}><div className="flex justify-between text-xs mb-1.5"><span className="text-gray-700 font-medium">{l.label}</span><span className="text-gray-400">{l.done?(l.error||"完成"):`${l.status||"..."} ${l.current}/${l.total}`}</span></div>
            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden"><div className={`h-full rounded-full transition-all duration-500 ${colors[i]||colors[0]}`} style={{width:`${l.percent}%`}}/></div></div>
          ))}
        </div>
      )}
      {p.allResults.filter(Boolean).length>0&&(
        <div className="mt-5 flex items-center gap-2 text-sm"><span className="text-gray-500 font-medium">查看</span>
        <select value={p.activeModelIdx} onChange={e=>p.viewModel(+e.target.value)} className="px-3 py-1.5 bg-white border border-gray-300 rounded-full text-sm text-black outline-none">
          {p.allResults.filter(Boolean).map((r:any,i:number)=><option key={i} value={i}>{r.label}（{(r.scenes||[]).length}场）</option>)}
        </select></div>
      )}
      {editing && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={()=>{setEditing(null);setAiResult("")}}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-3xl max-h-[90vh] flex flex-col shadow-xl" onClick={e=>e.stopPropagation()}>
            <h3 className="text-base font-bold text-black mb-3">编辑章节：{editing}</h3>
            <textarea id="chapter-editor" value={editText} onChange={e=>setEditText(e.target.value)}
              className="flex-1 min-h-[250px] px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-black resize-none outline-none"/>
            {aiResult && (
              <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-sm">
                <p className="text-xs text-gray-500 mb-2 font-medium">AI 处理结果（预览）：</p>
                <p className="text-gray-800 whitespace-pre-wrap">{aiResult}</p>
                <div className="flex gap-2 mt-2">
                  <button onClick={applyAiResult} className="px-3 py-1 bg-black text-white rounded-full text-xs font-medium">✅ 替换</button>
                  <button onClick={()=>setAiResult("")} className="px-3 py-1 border border-gray-300 rounded-full text-xs text-gray-500">取消</button>
                </div>
              </div>
            )}
            <div className="flex gap-3 mt-4 justify-between items-center">
              <div className="flex gap-2">
                <button onClick={()=>handleAiEdit("rewrite")} disabled={aiLoading}
                  className="px-3 py-1.5 border border-gray-300 rounded-full text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50">✨ 改写选中</button>
                <button onClick={()=>handleAiEdit("expand")} disabled={aiLoading}
                  className="px-3 py-1.5 border border-gray-300 rounded-full text-xs text-gray-600 hover:bg-gray-50 disabled:opacity-50">📝 扩写选中</button>
              </div>
              <div className="flex gap-3">
                <button onClick={()=>{setEditing(null);setAiResult("")}} className="px-5 py-2 border border-gray-300 rounded-full text-sm text-gray-600 hover:bg-gray-50">取消</button>
                <button onClick={()=>{p.setNovelText(editText);setEditing(null)}} className="px-5 py-2 bg-black text-white rounded-full text-sm font-medium hover:bg-gray-800">保存修改</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
