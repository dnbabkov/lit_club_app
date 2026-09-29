import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { getComicChapter, getComicChapters, getComicImage, type ComicChapter, type ComicChapterSummary } from "../api/comics"
import { useAuth } from "../auth/useAuth"
import { ComicImage } from "../components/ComicImage"
import { Layout } from "../components/Layout"
import "./comics.css"

export function ComicsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === "admin"
  const [chapters, setChapters] = useState<ComicChapterSummary[] | null>(null)
  const [error, setError] = useState("")
  useEffect(() => {
    let active = true
    getComicChapters().then(data => { if (active) setChapters(data) })
      .catch(error => { if (active) setError(error instanceof Error ? error.message : "Не удалось загрузить главы") })
    return () => { active = false }
  }, [])

  return <Layout>
    <div className="comic-toolbar"><h1>Комикс</h1>{isAdmin && <Link to="/comics/new">＋ Добавить главу</Link>}</div>
    {error ? <p role="alert">{error}</p> : chapters === null ? <p>Загрузка…</p> : chapters.length === 0 ? <p>Пока нет доступных глав.</p> :
      <div className="comic-grid">{chapters.map(chapter => <article className="comic-card" key={chapter.id}>
        <Link to={`/comics/${chapter.id}`}>
          <ComicImage path={chapter.cover_url} alt={`Обложка: ${chapter.title}`} className="comic-cover" />
          <h2>{chapter.number}. {chapter.title}</h2>
        </Link>
        <p>Страниц: {chapter.page_count}</p>
        {isAdmin && <><p>{chapter.is_public ? "Видна всем пользователям" : "Только для администратора"}</p><Link to={`/comics/${chapter.id}/edit`}>Редактировать</Link></>}
      </article>)}</div>}
  </Layout>
}

export function ComicReaderPage() {
  const { chapterId = "" } = useParams()
  return <ComicReader key={chapterId} chapterId={chapterId} />
}

function ComicReader({ chapterId }: { chapterId: string }) {
  const { user } = useAuth()
  const [chapter, setChapter] = useState<ComicChapter | null>(null)
  const [index, setIndex] = useState(0)
  const [error, setError] = useState("")
  const [pageImages, setPageImages] = useState<Record<string, string>>({})
  useEffect(() => {
    let active = true
    getComicChapter(chapterId).then(data => { if (active) setChapter(data) })
      .catch(error => { if (active) setError(error instanceof Error ? error.message : "Не удалось загрузить главу") })
    return () => { active = false }
  }, [chapterId])

  useEffect(() => {
    if (!chapter) return
    const controller = new AbortController()
    const createdUrls: string[] = []

    chapter.pages.forEach(page => {
      getComicImage(page.image_url, controller.signal).then(blob => {
        if (controller.signal.aborted) return
        const url = URL.createObjectURL(blob)
        createdUrls.push(url)
        setPageImages(current => ({ ...current, [page.image_url]: url }))
      }).catch(() => {
        // The visible page still has its own retry UI through ComicImage.
      })
    })

    return () => {
      controller.abort()
      createdUrls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [chapter])

  const count = chapter?.pages.length ?? 0
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.target instanceof HTMLInputElement) return
      if (event.key === "ArrowLeft") { event.preventDefault(); setIndex(value => Math.max(0, value - 1)) }
      if (event.key === "ArrowRight") { event.preventDefault(); setIndex(value => Math.min(Math.max(0, count - 1), value + 1)) }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [count])

  const navigation = <div className="comic-navigation">
    <button type="button" aria-label="Предыдущая страница" disabled={index === 0} onClick={() => setIndex(index - 1)}>← Назад</button>
    <span aria-live="polite">{index + 1}/{count}</span>
    <button type="button" aria-label="Следующая страница" disabled={index >= count - 1} onClick={() => setIndex(index + 1)}>Вперёд →</button>
  </div>

  return <Layout>
    <Link to="/comics">← Все главы</Link>
    {error ? <p role="alert">{error}</p> : !chapter ? <p>Загрузка…</p> : <>
      <div className="comic-toolbar"><h1>{chapter.number}. {chapter.title}</h1>{user?.role === "admin" && <Link to={`/comics/${chapter.id}/edit`}>Редактировать</Link>}</div>
      {count === 0 ? <p>В этой главе пока нет страниц.</p> : <>
        {navigation}
        <ComicImage key={chapter.pages[index].id} path={chapter.pages[index].image_url} preloadedUrl={pageImages[chapter.pages[index].image_url]} alt={`${chapter.title}, страница ${index + 1}`} className="comic-reader-image" />
        {navigation}
      </>}
    </>}
  </Layout>
}
