import type { BookRead } from "./books"

export type MeetingStatus =
  | "book_selection"
  | "scheduled"
  | "finished"

export type MeetingRead = {
  id: number
  status: MeetingStatus
  book_id: number | null
  scheduled_for: string | null
}

export type MeetingWithSelectionRead = {
  meeting: MeetingRead
  selection_id: number
}

export type MeetingCreatePayload = {
  status?: MeetingStatus | null
  book_id?: number | null
  scheduled_for?: string | null
}

export type MeetingScheduleUpdatePayload = {
  scheduled_for: string
}

export type MeetingWithBook = {
  meeting: MeetingRead
  book: BookRead | null
}