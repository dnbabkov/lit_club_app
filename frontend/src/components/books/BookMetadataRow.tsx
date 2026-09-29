type BookMetadataRowProps = {
  meetingDate: string | null
  averageRating: number | null
}

function formatMeetingDate(meetingDate: string | null): string {
  if (!meetingDate) {
    return "—"
  }

  const match = meetingDate.slice(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return match ? `${match[3]}.${match[2]}.${match[1]}` : meetingDate
}

function formatAverageRating(averageRating: number | null): string {
  return averageRating === null ? "—" : averageRating.toFixed(1)
}

export function BookMetadataRow({
  meetingDate,
  averageRating,
}: BookMetadataRowProps) {
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "8px 20px",
        color: "#444",
        marginTop: 12,
      }}
    >
      <span>
        <strong>Дата собрания:</strong> {formatMeetingDate(meetingDate)}
      </span>
      <span>
        <strong>Средний балл:</strong> {formatAverageRating(averageRating)}
      </span>
    </div>
  )
}
