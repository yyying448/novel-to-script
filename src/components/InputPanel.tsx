export default function InputPanel({ novelText, setNovelText, handleFile, handlePreview }: any) {
  const onDrop = (e: any) => {
    e.preventDefault()
    e.stopPropagation()
    const f = e.dataTransfer?.files?.[0]
    if (f) handleFile({ target: { files: [f] } })
  }
  const onDragOver = (e: any) => { e.preventDefault(); e.stopPropagation() }

  return (
    <div className="bg-[#0a0a0a] border border-zinc-800 rounded-2xl p-6 mb-5"
      onDrop={onDrop} onDragOver={onDragOver}>
      <h2 className="text-base font-semibold mb-5 text-white">输入小说</h2>
      <div className="border-2 border-dashed border-zinc-800 rounded-2xl p-12 text-center mb-4 hover:border-zinc-500 cursor-pointer transition-colors"
        onClick={() => document.getElementById("file-input")?.click()}>
        <p className="text-4xl mb-3 opacity-60">📂</p>
        <p className="text-zinc-500 text-sm">点击上传或拖拽文件到此处</p>
        <p className="text-zinc-600 text-xs mt-1">.txt / .docx / .pdf</p>
        <input id="file-input" type="file" accept=".txt,.docx,.pdf" className="hidden" onChange={handleFile} />
      </div>
      <textarea value={novelText} onChange={e => setNovelText(e.target.value)}
        placeholder="或直接粘贴小说全文..."
        onDrop={onDrop} onDragOver={onDragOver}
        className="w-full h-40 px-4 py-3 bg-black border border-zinc-800 rounded-xl text-sm text-white resize-y outline-none focus:border-white/40 transition-colors placeholder:text-zinc-600" />
      <button onClick={handlePreview}
        className="mt-4 px-6 py-2.5 bg-white text-black rounded-full text-sm font-medium hover:bg-zinc-200 transition-colors">预览章节</button>
    </div>
  )
}
