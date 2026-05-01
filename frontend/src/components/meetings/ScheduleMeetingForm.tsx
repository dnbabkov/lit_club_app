import { useState, type SyntheticEvent } from "react"
import { ApiError } from "../../api/http"
import { scheduleMeeting } from "../../api/meetings"

type ScheduleMeetingFormProps = {
  meetingId: number
  onSuccess: () => Promise<void> | void
}

export function ScheduleMeetingForm({
  meetingId,
  onSuccess,
}: ScheduleMeetingFormProps) {
  const [scheduledFor, setScheduledFor] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage("")
    setIsSubmitting(true)

    try {
      await scheduleMeeting(meetingId, {
        scheduled_for: scheduledFor,
      })

      setScheduledFor("")
      await onSuccess()
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginTop: 12 }}>
      <div style={{ marginBottom: 12 }}>
        <label htmlFor={`schedule-${meetingId}`}>Дата и время встречи</label>
        <input
          id={`schedule-${meetingId}`}
          type="datetime-local"
          value={scheduledFor}
          onChange={(event) => setScheduledFor(event.target.value)}
          style={{ display: "block", marginTop: 4, padding: 8 }}
        />
      </div>

      {errorMessage && (
        <p style={{ color: "crimson", marginBottom: 12 }}>{errorMessage}</p>
      )}

      <button type="submit" disabled={isSubmitting || !scheduledFor}>
        {isSubmitting ? "Сохраняем..." : "Назначить дату"}
      </button>
    </form>
  )
}