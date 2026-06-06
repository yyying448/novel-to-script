import type { ScriptResult, Scene, Character } from "../types"

const card = "bg-white border border-gray-200 rounded-2xl p-6 mb-5 shadow-sm"
const btn = "px-4 py-2 rounded-full text-sm font-medium transition-colors"

export function StrategyView({ report }: { report: string }) {
  if (!report) return <div className={card}><p className="text-gray-400 text-sm">改编策略将在转换过程中自动生成...</p></div>
  return <div className={card}><div className="text-sm leading-relaxed text-gray-700" dangerouslySetInnerHTML={{ __html:
    report.replace(/### (.*)/g,'<h3 class="text-black mt-4 mb-2 font-bold">$1</h3>').replace(/## (.*)/g,'<h2 class="text-gray-900 mt-5 mb-2 text-lg font-bold border-b border-gray-200 pb-1">$1</h2>').replace(/^- (.+)/gm,'<li class="ml-4 my-1 text-gray-600">$1</li>').replace(/\*\*(.*?)\*\*/g,"<b>$1</b>")
  }} /></div>
}

export function VisualView({ result }: { result: ScriptResult }) {
  const s = result.scenes || []
  if (!s.length) return <div className={card}><p className="text-gray-400 text-sm">暂无剧本，请先转换</p></div>
  const g: Record<string,Scene[]>={}; s.forEach(x=>{const c=x.chapter||"未分类";if(!g[c])g[c]=[];g[c].push(x)})
  return <div><p className="text-xs text-gray-500 mb-4 font-medium">共 {s.length} 场 · {Object.keys(g).length} 章</p>
    {Object.entries(g).map(([ch,chs])=>(<div key={ch} className={card+" !p-4"}><h3 className="text-sm font-bold text-gray-800 mb-4">📖 {ch} <span className="text-xs text-gray-400 ml-1 font-normal">{chs.length}场</span></h3>
      {chs.map(x=>(<div key={x.scene_id} className="bg-gray-50 border border-gray-100 rounded-xl p-4 mb-3 last:mb-0">
        <div className="flex items-center gap-2 flex-wrap mb-2"><span className="text-sm font-bold text-black">场景 {x.scene_id}</span><span className="text-xs text-gray-500">· {x.location||"?"}</span>{x.estimated_duration?<span className="text-xs text-gray-400">· {x.estimated_duration}分</span>:null}{x.dramatic_function?<span className="text-xs text-gray-500">· {x.dramatic_function}</span>:null}{x.conflict_intensity&&x.conflict_intensity>=3?<span className="text-[10px] bg-black text-white px-1.5 py-0.5 rounded-full font-bold">冲突 Lv{x.conflict_intensity}</span>:x.conflict_description?<span className="text-[10px] text-gray-500">🔥 {x.conflict_description}</span>:null}</div>
        {(x.difficulty_tags||[]).length>0&&<div className="flex gap-1 mb-2">{x.difficulty_tags!.map((t,i)=><span key={i} className="text-[10px] bg-gray-100 border border-gray-200 px-2 py-0.5 rounded-full text-gray-500">{t}</span>)}</div>}
        <p className="text-xs text-gray-500 mb-2">{x.summary}</p>
        {x.characters_present?.length?<p className="text-[10px] text-gray-400 mt-1">出场：{x.characters_present.filter(Boolean).map(c=>c.name).join("、")}</p>:null}
        {(x.dialogues||[]).map((d,i)=>(<div key={i} className="border-l-2 border-gray-300 pl-4 mt-3"><p className="text-sm font-bold text-gray-800">{d.speaker}</p>{(d.lines||[]).map((l,j)=><p key={j} className="text-sm text-gray-700 mt-0.5">{l}</p>)}{(d.tone||d.action)?<p className="text-[10px] text-gray-400 mt-1.5">{(d.tone?"🗣 "+d.tone:"")}{(d.tone&&d.action?" · ":"")}{(d.action?"🎭 "+d.action:"")}</p>:null}</div>))}
        {x.scene_notes?<p className="text-[10px] text-gray-400 mt-3 border-t border-gray-100 pt-2">📝 {x.scene_notes}</p>:null}
      </div>))}</div>))}
  </div>
}

export function CharactersView({ characters }: { characters: Character[] }) {
  if (!characters.length) return <div className={card}><p className="text-gray-400 text-sm">暂无角色数据，转换完成后自动生成</p></div>
  return <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {characters.map((c,i)=>(<div key={i} className={card+" !p-4"}>
      <h3 className="text-sm font-bold text-black mb-3">{c.role==="主角"?"⭐":c.role==="重要配角"?"🔶":"·"} {c.name}<span className="text-xs text-gray-400 ml-2 font-normal">{c.role}</span></h3>
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-500"><div>出场{c.chapters_count}章</div><div>场景{c.scene_count}次</div><div>台词{c.dialogue_count}句</div><div>首次{c.first_chapter}</div></div>
      {c.personality&&<p className="text-xs mt-3 pt-2 border-t border-gray-100 text-gray-700"><span className="font-bold text-gray-500">性格 </span>{c.personality}</p>}
      {c.motivation&&<p className="text-xs text-gray-600"><span className="font-bold text-gray-500">动机 </span>{c.motivation}</p>}
      {c.speech_style&&<p className="text-xs text-gray-600"><span className="font-bold text-gray-500">说话 </span>{c.speech_style}</p>}
      {c.identity&&<p className="text-xs text-gray-600"><span className="font-bold text-gray-500">身份 </span>{c.identity}</p>}
      {c.appearance&&<p className="text-xs text-gray-600"><span className="font-bold text-gray-500">外貌 </span>{c.appearance}</p>}
    </div>))}
  </div>
}

export function EpisodesView({ episodes, epMinutes }: any) {
  if (!episodes?.length) return <div className={card}><p className="text-gray-400 text-sm">{epMinutes>0?"⏳ 分集将在转换完成后自动生成...":"💡 设置单集时长后重新转换即可自动分集（如45分钟/集）"}</p></div>
  return <div>{episodes.map((ep:any)=>(<div key={ep.episode_id} className={card+" !p-0 overflow-hidden"}><h3 className="text-sm font-bold text-white bg-gray-900 px-5 py-3">📺 {ep.title}<span className="text-xs text-gray-400 ml-3 font-normal">{ep.scene_count}场 · {ep.estimated_duration}分</span></h3><p className="text-xs text-gray-500 px-5 py-2 bg-gray-50 border-b border-gray-100">{ep.summary}</p>{ep.scenes.map((s:Scene)=>(<div key={s.scene_id} className="text-xs py-2 px-5 border-b border-gray-100 last:border-0 flex gap-3"><span className="font-bold text-gray-500 whitespace-nowrap">{s.scene_id}</span><span className="text-gray-400">{s.location||"?"}</span><span className="text-gray-700 truncate">{s.summary}</span></div>))}</div>))}</div>
}

export function CompareView({ results, allResults, viewModel }: any) {
  if (!results?.length) return <div className={card}><p className="text-gray-400 text-sm">启用对比模式后，评分结果将在此展示</p></div>
  const max = Math.max(...results.map((r:any)=>{const s=r.score||{};return s.总分||Object.values(s).reduce((a:any,b:any)=>a+b,0)||0}))
  const best = results.find((r:any)=>{const s=r.score||{};const t=s.总分||Object.values(s).reduce((a:any,b:any)=>a+b,0)||0;return t>=max&&t>0})
  return <div className={card}><p className="text-xs text-gray-500 mb-3 font-medium">对话自然度 / 场景完整性 / 叙事流畅度 / 角色一致性 各 1-10 分</p>
  {best?<div className="bg-gray-900 text-white rounded-2xl p-4 mb-4 flex items-center gap-3"><span className="text-2xl">🏆</span><div><p className="font-bold text-sm">推荐使用 {best.label}</p><p className="text-xs text-gray-400 mt-0.5">综合评分最高，在四项指标上表现最优。你可随时切换查看其他模型结果。</p></div></div>:null}
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{results.map((r:any,i:number)=>{const s=r.score||{};const t=s.总分||Object.values(s).reduce((a:any,b:any)=>a+b,0)||0;const b=t>=max&&t>0;return(<div key={i} className={`bg-gray-50 border-2 rounded-2xl p-5 ${b?"border-black":"border-gray-200"}`}><h3 className="font-bold text-sm mb-3 text-black">{b?"★ ":""}{r.label}</h3><div className="text-xs space-y-1 text-gray-500"><div>{r.scene_count}场</div><div>评分 {JSON.stringify(s)}</div>{r.error?<div className="text-red-500">! {r.error}</div>:null}</div>{r.all_scenes?.length>0?<button onClick={()=>{const i=allResults.findIndex((x:any)=>x.label===r.label);if(i>=0)viewModel(i)}} className={`${btn} mt-3 !text-xs !px-3 !py-1.5 border border-gray-300 text-gray-600 hover:bg-gray-100`}>查看完整</button>:null}</div>)})}</div></div>
}

export function RevisePanel({ scriptResult, revChapter, setRevChapter, revFeedback, setRevFeedback, handleRevise }: any) {
  const chs=[...new Set((scriptResult.scenes||[]).map((s:Scene)=>s.chapter).filter(Boolean))] as string[]
  return <div className={card}><h2 className="text-base font-bold text-black mb-5">修改剧本</h2><div className="flex gap-3 mb-4 items-center"><label className="text-sm text-gray-500 font-medium">章节</label><select value={revChapter} onChange={e=>setRevChapter(e.target.value)} className="px-3 py-1.5 bg-white border border-gray-300 rounded-full text-sm text-black outline-none">{chs.map((c:string)=><option key={c} value={c}>{c.length>15?c.slice(0,15)+"…":c}</option>)}</select></div><textarea value={revFeedback} onChange={e=>setRevFeedback(e.target.value)} placeholder="描述需要修改的内容..." className="w-full h-24 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-black resize-y outline-none placeholder:text-gray-400"/><button onClick={handleRevise} className={`${btn} mt-4 bg-black text-white hover:bg-gray-800`}>应用修改</button></div>
}

export function YamlView({ result, runtime, sceneCount, charCount, epCount }: any) {
  return <div className={card}><p className="text-xs text-gray-500 mb-4 font-medium">{sceneCount}场 · {charCount}角色{epCount>0?` · ${epCount}集`:""}{runtime?.likely?` · ${runtime.likely}分`:""}</p><pre className="bg-gray-50 border border-gray-200 rounded-xl p-5 text-xs leading-relaxed overflow-x-auto max-h-[70vh] whitespace-pre-wrap text-gray-700">{yamlDump(result)}</pre></div>
}

function yamlDump(o:any,d=0):string{const p="  ".repeat(d);if(o===null||o===undefined)return"null";if(typeof o==="string")return(o.includes(":")||o.includes("#")||o.includes("'"))?`"${o}"`:o;if(typeof o==="number"||typeof o==="boolean")return String(o);if(Array.isArray(o)){if(o.length===0)return"[]";let s="";for(const i of o){if(typeof i==="object"&&i!==null){s+=`${p}- `;const n=yamlDump(i,d+1).trimStart();s+=n.startsWith("- ")?`\n${n}`:`${n}\n`}else s+=`${p}- ${yamlDump(i)}\n`}return s}let s="";for(const[k,v]of Object.entries(o)){if(v===null||v===undefined||v===""||(Array.isArray(v)&&v.length===0))s+=`${p}${k}: []\n`;else if(Array.isArray(v)&&v.length>0&&typeof v[0]!=="object")s+=`${p}${k}: [${v.map((x:any)=>yamlDump(x)).join(", ")}]\n`;else if(typeof v==="object"&&!Array.isArray(v))s+=`${p}${k}:\n${yamlDump(v,d+1)}`;else if(Array.isArray(v))s+=`${p}${k}:\n${yamlDump(v,d+1)}`;else s+=`${p}${k}: ${yamlDump(v)}\n`}return s}
