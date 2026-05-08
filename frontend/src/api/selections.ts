import { get, patch, post } from "./http"
import type {
  BookSelectionRead,
  CurrentSelectionRead,
  CurrentUserVotesRead,
  NominationBookUpdatePayload,
  NominationCommentUpdatePayload,
  NominationExistingBookChangePayload,
  NominationExistingBookCreatePayload,
  NominationNewBookChangePayload,
  NominationNewBookCreatePayload,
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

export async function createNominationFromExistingBook(
  selectionId: number,
  payload: NominationExistingBookCreatePayload
): Promise<NominationRead> {
  return post<NominationRead>(
    `/selections/${selectionId}/nominations/from-existing`,
    payload
  )
}

export async function createNominationFromNewBook(
  selectionId: number,
  payload: NominationNewBookCreatePayload
): Promise<NominationRead> {
  return post<NominationRead>(
    `/selections/${selectionId}/nominations/new`,
    payload
  )
}

export async function changeMyNominationToExistingBook(
  selectionId: number,
  payload: NominationExistingBookChangePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/change-book/from-existing`,
    payload
  )
}

export async function changeMyNominationToNewBook(
  selectionId: number,
  payload: NominationNewBookChangePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/change-book/new`,
    payload
  )
}

export async function updateMyNominationBook(
  selectionId: number,
  payload: NominationBookUpdatePayload
): Promise<NominationRead> {
  return patch<NominationRead>(
    `/selections/${selectionId}/nominations/me/edit-new-book`,
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