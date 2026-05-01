import type { NominationRead } from "../../types/selections"

type NominationsListProps = {
  nominations: NominationRead[]
}

export function NominationsList({ nominations }: NominationsListProps) {
    if (nominations.length === 0) {
        return <p>Пока нет предложенных книг.</p>
    }

    return (
        <ul style={{ padding: 0, listStyle: "none" }}>
          {nominations.map((nomination) => (
            <li
              key={nomination.id}
              style={{
                marginBottom: 12,
                padding: 12,
                border: "1px solid #ddd",
                borderRadius: 8,
              }}
            >
              <div>
                <strong>{nomination.title}</strong> — {nomination.author}
              </div>

              {nomination.comment && (
                <div style={{ marginTop: 6, fontSize: 14, color: "#555" }}>
                  {nomination.comment}
                </div>
              )}
            </li>
          ))}
        </ul>
    )
}