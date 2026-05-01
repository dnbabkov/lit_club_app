import type { BookSelectionStatus } from "../types/selections"

export function isNominationsOpen(status: BookSelectionStatus): boolean {
  return status === "nominations_open"
}

export function isVotingOpen(status: BookSelectionStatus): boolean {
  return status === "voting_open"
}

export function isVotingClosed(status: BookSelectionStatus): boolean {
  return status === "voting_closed"
}

export function isWinnerSelected(status: BookSelectionStatus): boolean {
  return status === "winner_selected"
}