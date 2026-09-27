import { useEffect, useState } from "react"
import { getComicImage } from "../api/comics"

export function ComicImage({ path, file, alt, className }: {
  path?: string | null; file?: File; alt: string; className?: string
}) {
  const [image, setImage] = useState<{ source: string | File; url: string } | null>(null)
  const [failed, setFailed] = useState<string | File | null>(null)
  const [attempt, setAttempt] = useState(0)
  const source = file ?? path

  useEffect(() => {
    if (!source) return
    const controller = new AbortController()
    let url: string | undefined
    const result = source instanceof File ? Promise.resolve(source) : getComicImage(source, controller.signal)
    result.then(blob => {
      if (controller.signal.aborted) return
      url = URL.createObjectURL(blob)
      setImage({ source, url })
      setFailed(null)
    }).catch(() => {
      if (!controller.signal.aborted) setFailed(source)
    })
    return () => { controller.abort(); if (url) URL.revokeObjectURL(url) }
  }, [source, attempt])

  if (!source) return <div className="comic-placeholder">Нет обложки</div>
  if (failed === source) return <div role="alert">Не удалось загрузить изображение. <button type="button" onClick={() => { setFailed(null); setAttempt(value => value + 1) }}>Повторить</button></div>
  if (image?.source !== source) return <div className="comic-placeholder" role="status">Загрузка изображения…</div>
  return <img className={className} src={image.url} alt={alt} onError={() => setFailed(source)} />
}
