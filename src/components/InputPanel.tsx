export default function InputPanel({ novelText, setNovelText, handleFile, handlePreview }: any) {
  const onDrop = (e: any) => {
    e.preventDefault(); e.stopPropagation()
    const f = e.dataTransfer?.files?.[0]
    if (f) handleFile({ target: { files: [f] } })
  }
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-5 shadow-sm"
      onDrop={onDrop} onDragOver={(e:any)=>{e.preventDefault();e.stopPropagation()}}>
      <h2 className="text-base font-bold text-black mb-5">输入小说</h2>
      <div className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center mb-4 hover:border-gray-500 cursor-pointer transition-colors"
        onClick={()=>document.getElementById("file-input")?.click()}>
        <p className="text-4xl mb-3 opacity-40">📂</p>
        <p className="text-gray-500 text-sm font-medium">点击上传或拖拽文件到此处</p>
        <p className="text-gray-400 text-xs mt-1">.txt / .docx / .pdf</p>
        <input id="file-input" type="file" accept=".txt,.docx,.pdf" className="hidden" onChange={handleFile}/>
      </div>
      <textarea value={novelText} onChange={e=>setNovelText(e.target.value)}
        placeholder="或直接粘贴小说全文..."
        onDrop={onDrop} onDragOver={(e:any)=>{e.preventDefault();e.stopPropagation()}}
        className="w-full h-40 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-black resize-y outline-none focus:border-black/30 placeholder:text-gray-400"/>
      <button onClick={handlePreview}
        className="mt-4 px-6 py-2.5 bg-black text-white rounded-full text-sm font-medium hover:bg-gray-800 transition-colors">预览章节</button>
    </div>
  )
}
