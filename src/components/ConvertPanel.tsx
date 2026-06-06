import type { Chapter } from "../types"

export default function ConvertPanel(p: any) {
  const c = ["bg-white", "bg-zinc-400", "bg-zinc-600"]
  return (
    <div className="bg-[#0a0a0a] border border-zinc-800 rounded-2xl p-6 mb-5">
      <h2 className="text-base font-semibold mb-5 text-white">转换</h2>
      {p.chapters.length > 0 && (
        <div className="mb-5">
          <p className="text-sm text-zinc-500 mb-3">识别到 {p.chapters.length} 个章节</p>
          <div className="flex flex-wrap gap-2">
            {p.chapters.map((ch: Chapter, i: number) => (
              <span key={i} className="px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-full text-xs text-zinc-400">{ch.title}<span className="text-zinc-600 ml-1">{ch.char_count}字</span></span>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-5">
            <label className="text-sm text-zinc-500">单集时长</label>
            <input type="number" value={p.epMinutes} onChange={e => p.setEpMinutes(Number(e.target.value)||0)} min={0} max={180}
              className="w-20 px-3 py-1.5 bg-black border border-zinc-800 rounded-full text-sm text-white text-center outline-none focus:border-white/40" />
            <span className="text-xs text-zinc-600">分钟（0=不分集）</span>
            <button onClick={p.handleConvert} disabled={p.converting}
              className="ml-auto px-6 py-2.5 bg-white text-black rounded-full text-sm font-medium hover:bg-zinc-200 disabled:opacity-30 transition-all">{p.converting ? "转换中..." : "开始转换"}</button>
          </div>
        </div>
      )}
      {p.lanes.length > 0 && (
        <div className="space-y-3">
          {p.lanes.map((l: any, i: number) => (
            <div key={i}>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-zinc-300">{l.label}</span>
                <span className="text-zinc-600">{l.done ? (l.error || "完成") : `${l.status || "..."} ${l.current}/${l.total}`}</span>
              </div>
              <div className="h-1 bg-zinc-900 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${c[i] || c[0]}`} style={{ width: `${l.percent}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
      {p.allResults.filter(Boolean).length > 0 && (
        <div className="mt-5 flex items-center gap-2 text-sm">
          <span className="text-zinc-500">查看</span>
          <select value={p.activeModelIdx} onChange={e => p.viewModel(+e.target.value)}
            className="px-3 py-1.5 bg-black border border-zinc-800 rounded-full text-sm text-white outline-none">
            {p.allResults.filter(Boolean).map((r: any, i: number) => (
              <option key={i} value={i}>{r.label}（{(r.scenes || []).length}场）</option>
            ))}
          </select>
        </div>
      )}
    </div>
  )
}
