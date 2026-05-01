import { useCallback, useEffect, useState, type SyntheticEvent } from "react"
import { Layout } from "../components/Layout"
import { useAuth } from "../auth/AuthContext"
import { ApiError } from "../api/http"
import {
  getCurrentSelection,
  getNominations,
  getVoteCounts,
  getMyVotesForSelection,
  voteForNominations,
  openVoting,
  closeVoting,
  startWinnerSelection,
  advanceWinnerSelectionStep,
  getWinnerSelectionState,
  finalizeWinnerSelection,
} from "../api/selections"
import type {
  CurrentSelectionRead,
  NominationRead,
  VoteCountRead,
  WinnerSelectionStateRead,
} from "../types/selections"
import { NominationsList } from "../components/selections/NominationsList"
import { NominationForm } from "../components/selections/NominationForm"
import { SelectionStatusBlock } from "../components/selections/SelectionStatusBlock"
import { VotingPanel } from "../components/selections/VotingPanel"
import { SelectionModeratorActions } from "../components/selections/SelectionModeratorActions"
import { WinnerStepsBlock } from "../components/selections/WinnerStepsBlock"

export function SelectionPage() {
  const { user } = useAuth()

  const [currentSelection, setCurrentSelection] = useState<CurrentSelectionRead | null>(null)
  const [nominations, setNominations] = useState<NominationRead[]>([])
  const [voteCounts, setVoteCounts] = useState<VoteCountRead[]>([])
  const [myVoteIds, setMyVoteIds] = useState<number[]>([])
  const [winnerState, setWinnerState] = useState<WinnerSelectionStateRead | null>(null)

  const [selectedNominationIds, setSelectedNominationIds] = useState<number[]>([])
  const [isEditingVote, setIsEditingVote] = useState(false)

  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  const loadSelectionData = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")

    try {
      const current = await getCurrentSelection()
      setCurrentSelection(current)

      if (current.selection_id === null) {
        setNominations([])
        setVoteCounts([])
        setMyVoteIds([])
        setSelectedNominationIds([])
        setWinnerState(null)
        setIsEditingVote(false)
        return
      }

      const nominationsData = await getNominations(current.selection_id)
      setNominations(nominationsData)

      if (
        current.selection_status === "voting_open" ||
        current.selection_status === "voting_closed" ||
        current.selection_status === "winner_selected"
      ) {
        const counts = await getVoteCounts(current.selection_id)
        setVoteCounts(counts)
      } else {
        setVoteCounts([])
      }

      if (current.selection_status === "voting_open") {
        const myVotes = await getMyVotesForSelection(current.selection_id)
        setMyVoteIds(myVotes.nomination_ids)
        setSelectedNominationIds(myVotes.nomination_ids)
        setIsEditingVote(false)
      } else {
        setMyVoteIds([])
        setSelectedNominationIds([])
        setIsEditingVote(false)
      }

      if (
        (current.selection_status === "voting_closed" ||
          current.selection_status === "winner_selected") &&
        current.winner_selection_session_id !== null
      ) {
        const state = await getWinnerSelectionState(current.winner_selection_session_id)
        setWinnerState(state)
      } else {
        setWinnerState(null)
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else if (error instanceof Error) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage("Unexpected error")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSelectionData()
  }, [loadSelectionData])

  async function handleVoteSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!currentSelection?.selection_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await voteForNominations(currentSelection.selection_id, {
        nomination_ids: selectedNominationIds,
      })
      await loadSelectionData()
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

  async function handleOpenVoting() {
    if (!currentSelection?.selection_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await openVoting(currentSelection.selection_id)
      await loadSelectionData()
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

  async function handleCloseVoting() {
    if (!currentSelection?.selection_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await closeVoting(currentSelection.selection_id)
      await loadSelectionData()
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

  async function handleStartWinnerSelection() {
    if (!currentSelection?.selection_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await startWinnerSelection(currentSelection.selection_id)
      await loadSelectionData()
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

  async function handleAdvanceWinnerSelection() {
    if (!winnerState?.session_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await advanceWinnerSelectionStep(winnerState.session_id)
      await loadSelectionData()
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

  async function handleFinalizeWinnerSelection() {
    if (!winnerState?.session_id) return

    setIsSubmitting(true)
    setErrorMessage("")

    try {
      await finalizeWinnerSelection(winnerState.session_id)
      await loadSelectionData()
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

  function handleStartEditingVote() {
    setSelectedNominationIds(myVoteIds)
    setIsEditingVote(true)
  }

  function toggleNominationSelection(nominationId: number) {
    setSelectedNominationIds((prev) =>
      prev.includes(nominationId)
        ? prev.filter((id) => id !== nominationId)
        : [...prev, nominationId]
    )
  }

  const myNomination = user
    ? nominations.find((nomination) => nomination.user_id === user.id)
    : null

  const isModerator = user?.role === "moderator"
  const userHasVoted = myVoteIds.length > 0

  function renderActiveSelection() {
    if (!currentSelection || currentSelection.selection_id === null) {
      return null
    }

    const selectionStatus = currentSelection.selection_status
    const hasWinnerSession = currentSelection.winner_selection_session_id !== null
    const winnerStateStatus = winnerState?.status ?? null

    if (selectionStatus === "nominations_open") {
      return (
        <>
          <p>Сейчас идёт этап предложения книг.</p>

          <NominationsList nominations={nominations} />

          {!myNomination && (
            <NominationForm
              selectionId={currentSelection.selection_id}
              onSuccess={loadSelectionData}
            />
          )}

          {isModerator && (
            <SelectionModeratorActions
              selectionStatus={selectionStatus}
              hasWinnerSession={hasWinnerSession}
              winnerStateStatus={winnerStateStatus}
              isSubmitting={isSubmitting}
              onOpenVoting={handleOpenVoting}
              onCloseVoting={handleCloseVoting}
              onStartWinnerSelection={handleStartWinnerSelection}
              onAdvanceWinnerSelection={handleAdvanceWinnerSelection}
              onFinalizeWinnerSelection={handleFinalizeWinnerSelection}
            />
          )}
        </>
      )
    }

    if (selectionStatus === "voting_open") {
      return (
        <>
          <VotingPanel
            nominations={nominations}
            voteCounts={voteCounts}
            selectedNominationIds={selectedNominationIds}
            userHasVoted={userHasVoted}
            isEditingVote={isEditingVote}
            isSubmitting={isSubmitting}
            onToggleNomination={toggleNominationSelection}
            onSubmit={handleVoteSubmit}
            onStartEditing={handleStartEditingVote}
          />

          {isModerator && (
            <SelectionModeratorActions
              selectionStatus={selectionStatus}
              hasWinnerSession={hasWinnerSession}
              winnerStateStatus={winnerStateStatus}
              isSubmitting={isSubmitting}
              onOpenVoting={handleOpenVoting}
              onCloseVoting={handleCloseVoting}
              onStartWinnerSelection={handleStartWinnerSelection}
              onAdvanceWinnerSelection={handleAdvanceWinnerSelection}
              onFinalizeWinnerSelection={handleFinalizeWinnerSelection}
            />
          )}
        </>
      )
    }

    if (selectionStatus === "voting_closed" || selectionStatus === "winner_selected") {
      return (
        <>
          {!hasWinnerSession ? (
            <>
              <p>Голосование завершено.</p>

              {isModerator && (
                <SelectionModeratorActions
                  selectionStatus={selectionStatus}
                  hasWinnerSession={hasWinnerSession}
                  winnerStateStatus={winnerStateStatus}
                  isSubmitting={isSubmitting}
                  onOpenVoting={handleOpenVoting}
                  onCloseVoting={handleCloseVoting}
                  onStartWinnerSelection={handleStartWinnerSelection}
                  onAdvanceWinnerSelection={handleAdvanceWinnerSelection}
                  onFinalizeWinnerSelection={handleFinalizeWinnerSelection}
                />
              )}
            </>
          ) : (
            <>
              <WinnerStepsBlock winnerState={winnerState} />

              {isModerator && (
                <SelectionModeratorActions
                  selectionStatus={selectionStatus}
                  hasWinnerSession={hasWinnerSession}
                  winnerStateStatus={winnerStateStatus}
                  isSubmitting={isSubmitting}
                  onOpenVoting={handleOpenVoting}
                  onCloseVoting={handleCloseVoting}
                  onStartWinnerSelection={handleStartWinnerSelection}
                  onAdvanceWinnerSelection={handleAdvanceWinnerSelection}
                  onFinalizeWinnerSelection={handleFinalizeWinnerSelection}
                />
              )}
            </>
          )}
        </>
      )
    }

    return <p>Неизвестный статус выбора книги.</p>
  }

  return (
    <Layout>
      <h1>Выбор книги</h1>

      {isLoading && <p>Загрузка...</p>}

      {!isLoading && errorMessage && (
        <p style={{ color: "crimson" }}>{errorMessage}</p>
      )}

      {!isLoading && !errorMessage && (
        <>
          {currentSelection?.selection_id === null ? (
            <SelectionStatusBlock currentSelection={currentSelection} />
          ) : (
            renderActiveSelection()
          )}
        </>
      )}
    </Layout>
  )
}