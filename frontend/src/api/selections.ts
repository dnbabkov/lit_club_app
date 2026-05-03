import { get, patch, post } from "./http"
import type {
  BookSelectionRead,
  CurrentSelectionRead,
  CurrentUserVotesRead,
  NominationBookUpdatePayload,
  NominationCommentUpdatePayload,
  NominationCreatePayload,
  NominationRead,
  VoteCountRead,
  VoteCreatePayload,
  WinnerSelectionStateRead,
  WinnerSelectRead,
} from "../types/selections"

export async function getCurrentSelection(): Promise<CurrentSelectionRead> {
  return get<CurrentSelectionRead>("/selections/current")
}

export async function getMyVotesForSelection(
  selectionId: number
): Promise<CurrentUserVotesRead> {
  return get<CurrentUserVotesRead>(`/selections/${selectionId}/votes/me`)
}

export async function getNominations(
  selectionId: number
): Promise<NominationRead[]> {
  return get<NominationRead[]>(`/selections/${selectionId}/nominations`)
}

export async function createNomination(
  selectionId: number,
  payload: NominationCreatePayload
): Promise<NominationRead> {
  return post<NominationRead>(
    `/selections/${selectionId}/nominations`,
    payload
  )
}

export async function updateMyNominationBook(
  selectionId: number,
  payload: NominationBookUpdatePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/book`,
    payload
  )
}

export async function changeMyNominationBook(
  selectionId: number,
  payload: NominationBookUpdatePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/change-book`,
    payload
  )
}

export async function updateMyNominationComment(
  selectionId: number,
  payload: NominationCommentUpdatePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/comment`,
    payload
  )
}

export async function openVoting(
  selectionId: number
): Promise<BookSelectionRead> {
  return post<BookSelectionRead>(`/selections/${selectionId}/open_voting`)
}

export async function closeVoting(
  selectionId: number
): Promise<BookSelectionRead> {
  return post<BookSelectionRead>(`/selections/${selectionId}/close_voting`)
}

export async function voteForNominations(
  selectionId: number,
  payload: VoteCreatePayload
): Promise<VoteCountRead[]> {
  return post<VoteCountRead[]>(`/selections/${selectionId}/votes`, payload)
}

export async function getVoteCounts(
  selectionId: number
): Promise<VoteCountRead[]> {
  return get<VoteCountRead[]>(`/selections/${selectionId}/votes`)
}

export async function startWinnerSelection(
  selectionId: number
): Promise<WinnerSelectionStateRead> {
  return post<WinnerSelectionStateRead>(
    `/selections/${selectionId}/winner-selection/start`
  )
}

export async function advanceWinnerSelectionStep(
  sessionId: number
): Promise<WinnerSelectionStateRead> {
  return post<WinnerSelectionStateRead>(
    `/selections/winner-selection/${sessionId}/advance`
  )
}

export async function getWinnerSelectionState(
  sessionId: number
): Promise<WinnerSelectionStateRead> {
  return get<WinnerSelectionStateRead>(
    `/selections/winner-selection/${sessionId}`
  )
}

export async function finalizeWinnerSelection(
  sessionId: number
): Promise<WinnerSelectRead> {
  return post<WinnerSelectRead>(
    `/selections/winner-selection/${sessionId}/finalize`
  )
}