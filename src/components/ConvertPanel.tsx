import { useState } from "react"
import type { Chapter } from "../types"

export default function ConvertPanel(p: any) {
  const [editing, setEditing] = useState<string | null>(null)
  const [editText, setEditText] = useState("")
  const colors = ["bg-black","bg-gray-500","bg-gray-300"]

  const openEdit = (ch: Chapter) => {
    // 从 novelText 中找该章节内容
    setEditing(ch.title)
    setEditText(p.chapterMap?.[ch.title] || "")
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
      {/* 章节编辑弹窗 */}
      {editing && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={()=>setEditing(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-3xl max-h-[80vh] flex flex-col shadow-xl" onClick={e=>e.stopPropagation()}>
            <h3 className="text-base font-bold text-black mb-3">编辑章节：{editing}</h3>
            <textarea value={editText} onChange={e => setEditText(e.target.value)}
              className="flex-1 min-h-[300px] px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-black resize-none outline-none"/>
            <div className="flex gap-3 mt-4 justify-end">
              <button onClick={()=>setEditing(null)} className="px-5 py-2 border border-gray-300 rounded-full text-sm text-gray-600 hover:bg-gray-50">取消</button>
              <button onClick={()=>{p.setNovelText(editText);setEditing(null)}} className="px-5 py-2 bg-black text-white rounded-full text-sm font-medium hover:bg-gray-800">保存修改</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
