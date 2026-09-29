import { useEffect, useState } from "react"
import { ApiError } from "../../api/http"
import { createQuote, deleteQuote, getQuotesForBook, updateQuote } from "../../api/quotes"
import type { QuoteRead } from "../../types/quotes"

type QuotesSectionProps = {
  bookId: number
  currentUserId: number | null
  isAdmin: boolean
}

function errorText(error: unknown): string {
  return error instanceof ApiError || error instanceof Error ? error.message : "Не удалось выполнить запрос"
}

export function QuotesSection({ bookId, currentUserId, isAdmin }: QuotesSectionProps) {
  const [quotes, setQuotes] = useState<QuoteRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [text, setText] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingText, setEditingText] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    getQuotesForBook(bookId)
      .then(result => { if (active) setQuotes(result) })
      .catch(reason => { if (active) setError(errorText(reason)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [bookId])

  async function addQuote() {
    if (loading) return
    const trimmed = text.trim()
    if (!trimmed) { setError("Введите текст цитаты"); return }
    setSaving(true); setError("")
    try {
      const quote = await createQuote({ book_id: bookId, text: trimmed })
      setQuotes(previous => [...previous, quote]); setText("")
    } catch (reason) { setError(errorText(reason)) } finally { setSaving(false) }
  }

  async function saveQuote(id: number) {
    const trimmed = editingText.trim()
    if (!trimmed) { setError("Введите текст цитаты"); return }
    setSaving(true); setError("")
    try {
      const quote = await updateQuote(id, { text: trimmed })
      setQuotes(previous => previous.map(item => item.id === id ? quote : item))
      setEditingId(null)
    } catch (reason) { setError(errorText(reason)) } finally { setSaving(false) }
  }

  async function removeQuote(quote: QuoteRead) {
    if (!window.confirm("Удалить эту цитату?")) return
    setError("")
    try { await deleteQuote(quote.id); setQuotes(previous => previous.filter(item => item.id !== quote.id)) }
    catch (reason) { setError(errorText(reason)) }
  }

  return <section aria-labelledby="quotes-title">
    <h2 id="quotes-title">Цитаты</h2>
    <div style={{ marginBottom: 20 }}>
      <label htmlFor="new-quote">Добавить цитату</label>
      <textarea id="new-quote" value={text} onChange={event => setText(event.target.value)} disabled={loading || saving} maxLength={10000} rows={4} style={{ display: "block", width: "100%", boxSizing: "border-box", margin: "6px 0" }} />
      <button type="button" onClick={addQuote} disabled={loading || saving}>Добавить цитату</button>
    </div>
    {error && <p role="alert" style={{ color: "crimson" }}>{error}</p>}
    {loading && <p role="status">Загрузка цитат...</p>}
    {!loading && !error && quotes.length === 0 && <p>Цитат пока нет.</p>}
    {!loading && quotes.map(quote => {
      const canManage = isAdmin || quote.user_id === currentUserId
      return <article key={quote.id} style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, marginBottom: 12 }}>
        <div style={{ marginBottom: 8, fontWeight: 500 }}>{quote.username}</div>
        {editingId === quote.id ? <>
          <textarea aria-label="Текст цитаты" value={editingText} onChange={event => setEditingText(event.target.value)} maxLength={10000} rows={4} style={{ display: "block", width: "100%", boxSizing: "border-box", marginBottom: 8 }} />
          <button type="button" onClick={() => saveQuote(quote.id)} disabled={saving}>Сохранить</button>{" "}
          <button type="button" onClick={() => setEditingId(null)}>Отмена</button>
        </> : <>
          <div style={{ whiteSpace: "pre-wrap", color: "#444", marginBottom: canManage ? 12 : 0 }}>{quote.text}</div>
          {canManage && <><button type="button" onClick={() => { setEditingId(quote.id); setEditingText(quote.text); setError("") }}>Изменить</button>{" "}<button type="button" onClick={() => removeQuote(quote)} style={{ color: "crimson" }}>Удалить</button></>}
        </>}
      </article>
    })}
  </section>
}
