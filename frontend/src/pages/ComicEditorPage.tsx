import { useEffect, useState, type FormEvent } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import { getComicChapter, saveComicChapter, type ComicChapter } from "../api/comics"
import { useAuth } from "../auth/useAuth"
import { ComicImage } from "../components/ComicImage"
import { Layout } from "../components/Layout"
import "./comics.css"

type DraftPage = { key: string; id?: number; number: number; image_url?: string; file?: File }
const imageTypes = "image/jpeg,image/png,image/webp"

export function ComicEditorPage() {
  const { chapterId } = useParams()
  const { user } = useAuth()
  if (user?.role !== "admin") return <Layout><h1>Нет доступа</h1><p>Редактировать комикс может только администратор.</p><Link to="/comics">Все главы</Link></Layout>
  return <EditorLoader key={chapterId ?? "new"} chapterId={chapterId} />
}

function EditorLoader({ chapterId }: { chapterId?: string }) {
  const [chapter, setChapter] = useState<ComicChapter | null>(null)
  const [error, setError] = useState("")
  useEffect(() => {
    if (!chapterId) return
    let active = true
    getComicChapter(chapterId).then(data => { if (active) setChapter(data) })
      .catch(error => { if (active) setError(error instanceof Error ? error.message : "Не удалось загрузить главу") })
    return () => { active = false }
  }, [chapterId])
  return <Layout>
    <Link to="/comics">← Все главы</Link>
    {error ? <p role="alert">{error}</p> : chapterId && !chapter ? <p>Загрузка…</p> : <ChapterEditor chapter={chapter} />}
  </Layout>
}

function ChapterEditor({ chapter }: { chapter: ComicChapter | null }) {
  const navigate = useNavigate()
  const [title, setTitle] = useState(chapter?.title ?? "")
  const [number, setNumber] = useState(chapter?.number ?? 1)
  const [isPublic, setIsPublic] = useState(chapter?.is_public ?? false)
  const [cover, setCover] = useState<File>()
  const [pages, setPages] = useState<DraftPage[]>(() => chapter?.pages.map(page => ({ ...page, key: String(page.id) })) ?? [])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")

  function validFile(file: File): boolean {
    if (!imageTypes.split(",").includes(file.type) || file.size > 20 * 1024 * 1024) {
      setError("Выберите изображение JPEG, PNG или WebP размером до 20 МБ")
      return false
    }
    setError("")
    return true
  }

  function changePage(key: string, update: Partial<DraftPage>) {
    setPages(previous => previous.map(page => page.key === key ? { ...page, ...update } : page))
  }

  function movePage(index: number, offset: number) {
    const reordered = [...pages]
    ;[reordered[index], reordered[index + offset]] = [reordered[index + offset], reordered[index]]
    setPages(reordered.map((page, index) => ({ ...page, number: index + 1 })))
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    if (new Set(pages.map(page => page.number)).size !== pages.length) {
      setError("Номера страниц не должны повторяться")
      return
    }
    setBusy(true)
    setError("")
    const data = new FormData()
    let fileIndex = 0
    const pageData = pages.map(page => {
      const result = { id: page.id, number: page.number, file_index: page.file ? fileIndex++ : undefined }
      if (page.file) data.append("files", page.file)
      return result
    })
    data.append("payload", JSON.stringify({ title: title.trim(), number, is_public: isPublic, pages: pageData }))
    if (cover) data.append("cover", cover)
    try {
      await saveComicChapter(chapter?.id ?? null, data)
      navigate("/comics")
    } catch (error) {
      setError(error instanceof Error ? error.message : "Не удалось сохранить главу")
      setBusy(false)
    }
  }

  return <form onSubmit={save} className="comic-editor">
    <h1>{chapter ? "Редактирование главы" : "Добавить главу"}</h1>
    <p>Изменения применяются после нажатия «Сохранить главу».</p>
    <fieldset disabled={busy}>
      <label>Название главы<input required maxLength={200} value={title} onChange={event => setTitle(event.target.value)} /></label>
      <label>Номер главы<input required type="number" min={1} max={2147483647} value={number || ""} onChange={event => setNumber(Number(event.target.value))} /></label>
      <label>Видимость<select value={isPublic ? "public" : "private"} onChange={event => setIsPublic(event.target.value === "public")}>
        <option value="private">Только администратору</option><option value="public">Всем пользователям</option>
      </select></label>
      <label>Обложка<input type="file" accept={imageTypes} onChange={event => {
        const file = event.target.files?.[0]
        if (file && validFile(file)) setCover(file)
        event.target.value = ""
      }} /></label>
      <ComicImage file={cover} path={chapter?.cover_url} alt="Обложка главы" className="comic-editor-preview" />
      <h2>Страницы ({pages.length})</h2>
      <p>Задайте номера или используйте стрелки для перестановки. Изображения: JPEG, PNG, WebP, до 20 МБ каждое.</p>
      {pages.length === 0 && <p>Добавьте первую страницу главы.</p>}
      <div className="comic-editor-pages">{pages.map((page, index) => <div className="comic-editor-page" key={page.key}>
        <ComicImage file={page.file} path={page.image_url} alt={`Страница ${page.number}`} className="comic-editor-preview" />
        <div>
          <label>Номер страницы<input type="number" required min={1} max={2147483647} value={page.number || ""} onChange={event => changePage(page.key, { number: Number(event.target.value) })} /></label>
          <label>Заменить изображение<input type="file" accept={imageTypes} onChange={event => {
            const file = event.target.files?.[0]
            if (file && validFile(file)) changePage(page.key, { file })
            event.target.value = ""
          }} /></label>
          <div className="comic-toolbar">
            <button type="button" aria-label={`Переместить страницу ${index + 1} вверх`} disabled={index === 0} onClick={() => movePage(index, -1)}>↑</button>
            <button type="button" aria-label={`Переместить страницу ${index + 1} вниз`} disabled={index === pages.length - 1} onClick={() => movePage(index, 1)}>↓</button>
            <button type="button" onClick={() => setPages(previous => previous.filter(item => item.key !== page.key))}>Удалить страницу</button>
          </div>
        </div>
      </div>)}</div>
      <label className="comic-add-page">＋ Добавить страницу<input type="file" accept={imageTypes} onChange={event => {
        const file = event.target.files?.[0]
        if (file && validFile(file)) setPages(previous => [...previous, { key: crypto.randomUUID(), number: Math.max(0, ...previous.map(page => page.number)) + 1, file }])
        event.target.value = ""
      }} /></label>
      <button type="button" onClick={() => setPages(previous => [...previous].sort((a, b) => a.number - b.number))}>Упорядочить по номерам</button>
      <div className="comic-toolbar"><button type="submit">{busy ? "Сохранение…" : "Сохранить главу"}</button><button type="button" onClick={() => navigate("/comics")}>Отмена</button></div>
    </fieldset>
    {error && <p role="alert">{error}</p>}
    {busy && <p role="status">Загружаем изображения и сохраняем главу…</p>}
  </form>
}
