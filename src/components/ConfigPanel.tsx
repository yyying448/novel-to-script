import type { Provider } from "../types"
import * as api from "../lib/api"

const inputCls = "w-full px-3 py-2 bg-black border border-zinc-800 rounded-full text-sm text-white outline-none focus:border-white/50 transition-colors"
const selCls = "px-3 py-2 bg-black border border-zinc-800 rounded-full text-sm text-white outline-none"

export default function ConfigPanel(p: any) {
  return (
    <div className="bg-[#0a0a0a] border border-zinc-800 rounded-2xl p-6 mb-5">
      <h2 className="text-base font-semibold mb-5 text-white">配置 LLM</h2>
      <div className="flex gap-3 mb-3 flex-wrap">
        <select value={p.provider} onChange={(e: any) => { p.setProvider(e.target.value); p.setModel("") }}
          className={selCls}>
          {p.providers.map((pr: Provider) => <option key={pr.key} value={pr.key}>{pr.name}</option>)}
        </select>
        <input type="text" value={p.model} onChange={(e: any) => p.setModel(e.target.value)}
          placeholder={`模型: ${p.providers.find((x: any) => x.key === p.provider)?.model || "?"}`} className={inputCls} />
        <input type="password" value={p.apiKey} onChange={(e: any) => p.setApiKey(e.target.value)}
          placeholder="API Key" className={inputCls + " flex-1 min-w-[200px]"} />
        <button onClick={p.handleSaveKey}
          className="px-5 py-2 bg-white text-black rounded-full text-sm font-medium hover:bg-zinc-200 transition-colors">验证</button>
      </div>
      {p.provider === "custom" && <input type="text" value={p.customUrl} onChange={(e: any) => p.setCustomUrl(e.target.value)} placeholder="自定义 API 地址" className={inputCls + " mb-3"} />}
      <details className="mt-3">
        <summary className="text-sm text-zinc-500 cursor-pointer hover:text-zinc-300">对比模式（可选）</summary>
        <div className="flex gap-2 mt-3 flex-wrap">
          <input type="text" value={p.cmpKeyB} onChange={(e: any) => p.setCmpKeyB(e.target.value)} placeholder="模型 B Key" className={inputCls} />
          <input type="text" value={p.cmpModelB} onChange={(e: any) => p.setCmpModelB(e.target.value)} placeholder="模型 B 名" className={inputCls + " w-32"} />
          <select value={p.cmpProvB} onChange={(e: any) => p.setCmpProvB(e.target.value)} className={selCls}>
            {["openai", "deepseek", "zhipu", "moonshot", "qwen"].map(v => <option key={v} value={v}>{v}</option>)}
          </select>
          <button onClick={() => api.validateKey(p.cmpKeyB, p.cmpProvB).then((r: any) => p.showToast(r.success ? "✅ 模型 B OK" : "❌ " + r.message))}
            className="px-3 py-2 text-sm border border-zinc-700 text-zinc-300 rounded-full hover:bg-zinc-900 transition-colors">验证</button>
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          <input type="text" value={p.cmpKeyC} onChange={(e: any) => p.setCmpKeyC(e.target.value)} placeholder="模型 C Key（可选）" className={inputCls} />
          <input type="text" value={p.cmpModelC} onChange={(e: any) => p.setCmpModelC(e.target.value)} placeholder="模型 C 名" className={inputCls + " w-32"} />
          <select value={p.cmpProvC} onChange={(e: any) => p.setCmpProvC(e.target.value)} className={selCls}>
            {["openai", "deepseek", "zhipu", "moonshot", "qwen"].map(v => <option key={v} value={v}>{v}</option>)}
          </select>
          <button onClick={() => api.validateKey(p.cmpKeyC, p.cmpProvC).then((r: any) => p.showToast(r.success ? "✅ 模型 C OK" : "❌ " + r.message))}
            className="px-3 py-2 text-sm border border-zinc-700 text-zinc-300 rounded-full hover:bg-zinc-900 transition-colors">验证</button>
        </div>
      </details>
    </div>
  )
}
