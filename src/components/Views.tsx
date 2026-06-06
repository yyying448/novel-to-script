import type { ScriptResult, Scene, Character } from "../types"

function Card({ children, className }: any) { return <div className={`bg-[#0a0a0a] border border-zinc-800 rounded-2xl p-6 mb-5 ${className||""}`}>{children}</div> }
function Btn({ children, onClick, variant, className }: any) {
  const c = variant === "outline" ? "border border-zinc-700 text-zinc-300 hover:bg-zinc-900" : "bg-white text-black hover:bg-zinc-200"
  return <button onClick={onClick} className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${c} ${className||""}`}>{children}</button>
}

export function StrategyView({ report }: { report: string }) {
  if (!report) return <Card><p className="text-zinc-500 text-sm">改编策略将在转换过程中自动生成...</p></Card>
  return <Card><div className="text-sm leading-relaxed text-zinc-300" dangerouslySetInnerHTML={{ __html:
    report.replace(/### (.*)/g,'<h3 class="text-white mt-4 mb-2 font-semibold">$1</h3>').replace(/## (.*)/g,'<h2 class="text-zinc-200 mt-5 mb-2 text-lg font-bold border-b border-zinc-800 pb-1">$1</h2>').replace(/^- (.+)/gm,'<li class="ml-4 my-1 text-zinc-400">$1</li>').replace(/\*\*(.*?)\*\*/g,"<b>$1</b>")
  }} /></Card>
}

export function VisualView({ result }: { result: ScriptResult }) {
  const scenes = result.scenes || []
  if (!scenes.length) return <Card><p className="text-zinc-500 text-sm">暂无剧本，请先转换</p></Card>
  const groups: Record<string, Scene[]> = {}
  scenes.forEach(s => { const c = s.chapter || "未分类"; if (!groups[c]) groups[c] = []; groups[c].push(s) })
  return (
    <div>
      <p className="text-xs text-zinc-600 mb-4">共 {scenes.length} 场 · {Object.keys(groups).length} 章</p>
      {Object.entries(groups).map(([ch, chs]) => (
        <Card key={ch} className="!p-4">
          <h3 className="text-sm font-semibold text-zinc-300 mb-4">📖 {ch} <span className="text-xs text-zinc-600 ml-1">{chs.length}场</span></h3>
          {chs.map(s => (
            <div key={s.scene_id} className="bg-black border border-zinc-800 rounded-xl p-4 mb-3 last:mb-0">
              <div className="flex items-center gap-2 flex-wrap mb-2">
                <span className="text-sm font-semibold text-white">场景 {s.scene_id}</span>
                <span className="text-xs text-zinc-500">· {s.location || "?"}</span>
                {s.estimated_duration ? <span className="text-xs text-zinc-600">· {s.estimated_duration}分</span> : null}
                {s.dramatic_function ? <span className="text-xs text-zinc-400">· {s.dramatic_function}</span> : null}
                {s.conflict_intensity && s.conflict_intensity >= 3
                  ? <span className="text-[10px] bg-white text-black px-1.5 py-0.5 rounded-full font-medium">冲突 Lv{s.conflict_intensity}</span>
                  : s.conflict_description ? <span className="text-[10px] text-zinc-400">🔥 {s.conflict_description}</span> : null}
              </div>
              {(s.difficulty_tags || []).length > 0 && <div className="flex gap-1 mb-2">{s.difficulty_tags!.map((t,i)=><span key={i} className="text-[10px] bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-full text-zinc-400">{t}</span>)}</div>}
              <p className="text-xs text-zinc-500 mb-2">{s.summary}</p>
              {s.characters_present?.length ? <p className="text-[10px] text-zinc-600 mt-1">出场：{s.characters_present.filter(Boolean).map(c=>c.name).join("、")}</p> : null}
              {(s.dialogues||[]).map((d,i)=>(<div key={i} className="border-l border-zinc-800 pl-4 mt-3"><p className="text-sm font-semibold text-zinc-300">{d.speaker}</p>{(d.lines||[]).map((l,j)=><p key={j} className="text-sm text-zinc-200 mt-0.5">{l}</p>)}{(d.tone||d.action)?<p className="text-[10px] text-zinc-600 mt-1.5">{(d.tone?"🗣 "+d.tone:"")}{(d.tone&&d.action?" · ":"")}{(d.action?"🎭 "+d.action:"")}</p>:null}</div>))}
              {s.scene_notes ? <p className="text-[10px] text-zinc-500 mt-3 border-t border-zinc-900 pt-2">📝 {s.scene_notes}</p> : null}
            </div>
          ))}
        </Card>
      ))}
    </div>
  )
}

export function CharactersView({ characters }: { characters: Character[] }) {
  if (!characters.length) return <Card><p className="text-zinc-500 text-sm">暂无角色数据</p></Card>
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {characters.map((c,i)=>(
        <Card key={i} className="!p-4">
          <h3 className="text-sm font-semibold text-white mb-3">{c.role==="主角"?"⭐":c.role==="重要配角"?"🔶":"·"} {c.name}<span className="text-xs text-zinc-600 ml-2">{c.role}</span></h3>
          <div className="grid grid-cols-2 gap-2 text-xs text-zinc-500"><div>出场{c.chapters_count}章</div><div>场景{c.scene_count}次</div><div>台词{c.dialogue_count}句</div><div>首次{c.first_chapter}</div></div>
          {c.personality&&<p className="text-xs mt-2 text-zinc-300"><b className="text-zinc-500">性格 </b>{c.personality}</p>}
          {c.motivation&&<p className="text-xs text-zinc-400"><b className="text-zinc-500">动机 </b>{c.motivation}</p>}
          {c.speech_style&&<p className="text-xs text-zinc-400"><b className="text-zinc-500">说话 </b>{c.speech_style}</p>}
          {c.identity&&<p className="text-xs text-zinc-400"><b className="text-zinc-500">身份 </b>{c.identity}</p>}
          {c.appearance&&<p className="text-xs text-zinc-400"><b className="text-zinc-500">外貌 </b>{c.appearance}</p>}
          {Object.keys(c.relationships).length>0&&<p className="text-xs text-zinc-500 mt-1"><b className="text-zinc-600">关系 </b>{Object.entries(c.relationships).map(([k,v])=>`${k}→${v}`).join(" · ")}</p>}
        </Card>
      ))}
    </div>
  )
}

export function EpisodesView({ episodes, epMinutes }: any) {
  if (!episodes?.length) return <Card><p className="text-zinc-500 text-sm">{epMinutes>0?"⏳ 分集将在转换完成后自动生成...":"💡 设置单集时长后重新转换即可自动分集（如45分钟/集）"}</p></Card>
  return <div>{episodes.map((ep:any)=>(<Card key={ep.episode_id} className="!p-0 overflow-hidden"><h3 className="text-sm font-semibold text-white bg-zinc-900 px-5 py-3 border-b border-zinc-800">📺 {ep.title}<span className="text-xs text-zinc-500 ml-3">{ep.scene_count}场 · {ep.estimated_duration}分</span></h3><p className="text-xs text-zinc-500 px-5 py-2 bg-black border-b border-zinc-900">{ep.summary}</p>{ep.scenes.map((s:Scene)=>(<div key={s.scene_id} className="text-xs py-2 px-5 border-b border-zinc-900 last:border-0 flex gap-3"><span className="font-medium text-zinc-400 whitespace-nowrap">{s.scene_id}</span><span className="text-zinc-600">{s.location||"?"}</span><span className="text-zinc-300 truncate">{s.summary}</span></div>))}</Card>))}</div>
}

export function CompareView({ results, allResults, viewModel }: any) {
  if (!results?.length) return <Card><p className="text-zinc-500 text-sm">启用对比模式后，评分结果将在此展示</p></Card>
  const maxScore = Math.max(...results.map((r:any)=>{const s=r.score||{};return s.总分||Object.values(s).reduce((a:any,b:any)=>a+b,0)||0}))
  return (<Card><p className="text-xs text-zinc-600 mb-4">对话自然度 / 场景完整性 / 叙事流畅度 / 角色一致性 各 1-10 分</p><div className="grid grid-cols-1 md:grid-cols-3 gap-4">{results.map((r:any,i:number)=>{const s=r.score||{};const t=s.总分||Object.values(s).reduce((a:any,b:any)=>a+b,0)||0;const best=t>=maxScore&&t>0;return(<div key={i} className={`bg-black border-2 rounded-2xl p-5 ${best?"border-white":"border-zinc-800"}`}><h3 className="font-semibold text-sm mb-3 text-white">{best?"★ ":""}{r.label}</h3><div className="text-xs space-y-1 text-zinc-500"><div>{r.scene_count}场</div><div>评分 {JSON.stringify(s)}</div>{r.error?<div className="text-red-400">! {r.error}</div>:null}</div>{r.preview?.length>0?<div className="mt-3 text-xs text-zinc-400 space-y-0.5">{r.preview.map((s:any)=><div key={s.scene_id}>— {s.summary}</div>)}</div>:null}{r.all_scenes?.length>0?<Btn variant="outline" className="mt-3 !text-xs !px-3 !py-1.5" onClick={()=>{const i=allResults.findIndex((x:any)=>x.label===r.label);if(i>=0)viewModel(i)}}>查看完整</Btn>:null}</div>)})}</div></Card>)
}

export function RevisePanel({ scriptResult, revChapter, setRevChapter, revFeedback, setRevFeedback, handleRevise }: any) {
  const chs = [...new Set((scriptResult.scenes||[]).map((s:Scene)=>s.chapter).filter(Boolean))] as string[]
  return (<Card><h2 className="text-base font-semibold mb-5 text-white">修改剧本</h2><div className="flex gap-3 mb-4 items-center"><label className="text-sm text-zinc-500">章节</label><select value={revChapter} onChange={e=>setRevChapter(e.target.value)} className="px-3 py-1.5 bg-black border border-zinc-800 rounded-full text-sm text-white outline-none">{chs.map((c:string)=><option key={c} value={c}>{c.length>15?c.slice(0,15)+"…":c}</option>)}</select></div><textarea value={revFeedback} onChange={e=>setRevFeedback(e.target.value)} placeholder="描述需要修改的内容..." className="w-full h-24 px-4 py-3 bg-black border border-zinc-800 rounded-xl text-sm text-white resize-y outline-none focus:border-white/40 placeholder:text-zinc-600"/><Btn onClick={handleRevise} className="mt-4">应用修改</Btn></Card>)
}

export function YamlView({ result, runtime, sceneCount, charCount, epCount }: any) {
  return (<Card><p className="text-xs text-zinc-600 mb-4">{sceneCount}场 · {charCount}角色{epCount>0?` · ${epCount}集`:""}{runtime?.likely?` · ${runtime.likely}分`:""}</p><pre className="bg-black border border-zinc-800 rounded-xl p-5 text-xs leading-relaxed overflow-x-auto max-h-[70vh] whitespace-pre-wrap text-zinc-300">{yamlDump(result)}</pre></Card>)
}

function yamlDump(o:any,d=0):string{const p="  ".repeat(d);if(o===null||o===undefined)return"null";if(typeof o==="string")return(o.includes(":")||o.includes("#")||o.includes("'"))?`"${o}"`:o;if(typeof o==="number"||typeof o==="boolean")return String(o);if(Array.isArray(o)){if(o.length===0)return"[]";let s="";for(const i of o){if(typeof i==="object"&&i!==null){s+=`${p}- `;const n=yamlDump(i,d+1).trimStart();s+=n.startsWith("- ")?`\n${n}`:`${n}\n`}else s+=`${p}- ${yamlDump(i)}\n`}return s}let s="";for(const[k,v]of Object.entries(o)){if(v===null||v===undefined||v===""||(Array.isArray(v)&&v.length===0))s+=`${p}${k}: []\n`;else if(Array.isArray(v)&&v.length>0&&typeof v[0]!=="object")s+=`${p}${k}: [${v.map((x:any)=>yamlDump(x)).join(", ")}]\n`;else if(typeof v==="object"&&!Array.isArray(v))s+=`${p}${k}:\n${yamlDump(v,d+1)}`;else if(Array.isArray(v))s+=`${p}${k}:\n${yamlDump(v,d+1)}`;else s+=`${p}${k}: ${yamlDump(v)}\n`}return s}
