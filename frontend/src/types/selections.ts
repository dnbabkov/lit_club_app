export type BookSelectionStatus =
  | "nominations_open"
  | "voting_open"
  | "voting_closed"
  | "winner_selected"

export type NominationRead = {
  id: number
  user_id: number
  selection_id: number
  book_id: number
  title: string
  author: string
  comment: string | null
}

export type BookSelectionRead = {
  id: number
  meeting_id: number
  status: BookSelectionStatus
  winning_nomination_id: number | null
}

export type CurrentSelectionRead = {
  selection_id: number | null
  meeting_id: number | null
  meeting_status: "book_selection" | "scheduled" | "finished" | null
  selection_status: BookSelectionStatus | null
  winner_selection_session_id: number | null
}

export type VoteCountRead = {
  nomination_id: number
  vote_count: number
}

export type NominationCreatePayload = {
  title: string
  author: string
  comment: string | null
}

export type NominationBookUpdatePayload = {
  title: string
  author: string
}

export type NominationUpdatePayload = {
  title: string
  author: string
  comment: string | null
}

export type NominationCommentUpdatePayload = {
  comment: string | null
}

export type VoteCreatePayload = {
  nomination_ids: number[]
}

export type CurrentUserVotesRead = {
  nomination_ids: number[]
}

export type WinnerSelectionStateRead = {
  session_id: number
  selection_id: number
  status: "in_progress" | "ready_to_finalize" | "finalized"
  current_round: number
  winner_nomination_id: number | null
  steps: WinnerSelectionStepRead[]
}

export type WinnerSelectionStepRead = {
  step_id: number
  round_number: number
  eliminated_nomination_id: number
  candidates: WinnerSelectionStepCandidateRead[]
}

export type WinnerSelectionStepCandidateRead = {
  nomination_id: number
  vote_count: number
  elimination_weight: number
  elimination_probability: number
  was_eliminated: boolean
}

export type WinnerSelectRead = {
  selection_id: number
  winning_nomination_id: number
  book_id: number
  title: string
  author: string
  description: string | null
  vote_count: number
}