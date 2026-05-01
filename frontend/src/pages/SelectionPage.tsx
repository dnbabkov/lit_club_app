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

export function SelectionPage() {
  const { user } = useAuth()

  const [currentSelection, setCurrentSelection] = useState<CurrentSelectionRead | null>(null)
  const [nominations, setNominations] = useState<NominationRead[]>([])
  const [voteCounts, setVoteCounts] = useState<VoteCountRead[]>([])
  const [myVoteIds, setMyVoteIds] = useState<number[]>([])
  const [winnerState, setWinnerState] = useState<WinnerSelectionStateRead | null>(null)

  const [selectedNominationIds, setSelectedNominationIds] = useState<number[]>([])

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
        setWinnerState(null)
        return
      }

      const nominationsData = await getNominations(current.selection_id)
      setNominations(nominationsData)

      if (current.selection_status === "voting_open" || current.selection_status === "voting_closed" || current.selection_status === "winner_selected") {
        const counts = await getVoteCounts(current.selection_id)
        setVoteCounts(counts)
      } else {
        setVoteCounts([])
      }

      if (current.selection_status === "voting_open") {
        const myVotes = await getMyVotesForSelection(current.selection_id)
        setMyVoteIds(myVotes.nomination_ids)
        setSelectedNominationIds(myVotes.nomination_ids)
      } else {
        setMyVoteIds([])
        setSelectedNominationIds([])
      }

      if (
        (current.selection_status === "voting_closed" || current.selection_status === "winner_selected") &&
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

  function renderNoActiveSelection() {
    if (!currentSelection) {
      return <p>Нет данных о текущем выборе книги.</p>
    }

    if (currentSelection.meeting_status === "scheduled") {
      return <p>Выбор книги завершён.</p>
    }

    if (currentSelection.meeting_status === "finished") {
      return <p>Выбор книги не начат.</p>
    }

    if (currentSelection.meeting_status === null) {
      return <p>Встреч пока нет.</p>
    }

    return <p>Текущий выбор книги отсутствует.</p>
  }

  function renderVotingStage() {
    const countByNominationId = new Map(voteCounts.map((item) => [item.nomination_id, item.vote_count]))
    const userHasVoted = myVoteIds.length > 0

    return (
      <>
        <p>Сейчас идёт голосование.</p>

        <form onSubmit={handleVoteSubmit}>
          <ul style={{ listStyle: "none", padding: 0 }}>
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
                <label style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  {!userHasVoted && (
                    <input
                      type="checkbox"
                      checked={selectedNominationIds.includes(nomination.id)}
                      onChange={() => toggleNominationSelection(nomination.id)}
                    />
                  )}

                  <div>
                    <div>
                      <strong>{nomination.title}</strong> — {nomination.author}
                    </div>
                    <div style={{ fontSize: 14, color: "#555" }}>
                      Голосов: {countByNominationId.get(nomination.id) ?? 0}
                    </div>
                  </div>
                </label>
              </li>
            ))}
          </ul>

          {!userHasVoted && (
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Отправляем..." : "Проголосовать"}
            </button>
          )}
        </form>

        {isModerator && (
          <div style={{ marginTop: 24 }}>
            <button onClick={handleCloseVoting} disabled={isSubmitting}>
              Завершить голосование
            </button>
          </div>
        )}
      </>
    )
  }

  function renderWinnerSteps() {
    return (
      <>
        <p>Голосование завершено. Идёт определение победителя.</p>

        {winnerState?.steps.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {winnerState.steps.map((step) => (
              <div
                key={step.step_id}
                style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}
              >
                <h3>Шаг {step.round_number}</h3>

                <ul>
                  {step.candidates.map((candidate) => (
                    <li key={candidate.nomination_id}>
                      Номинация #{candidate.nomination_id}: {candidate.vote_count} голосов, шанс вылета{" "}
                      {(candidate.elimination_probability * 100).toFixed(1)}%
                      {candidate.was_eliminated ? " — выбыла" : ""}
                    </li>
                  ))}
                </ul>

                <p>
                  Вылетел кандидат: <strong>{step.eliminated_nomination_id}</strong>
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p>Шагов пока нет.</p>
        )}

        {winnerState?.winner_nomination_id && (
          <p>
            Победившая номинация: <strong>{winnerState.winner_nomination_id}</strong>
          </p>
        )}

        {isModerator && winnerState?.status === "in_progress" && (
          <button onClick={handleAdvanceWinnerSelection} disabled={isSubmitting}>
            Следующий шаг
          </button>
        )}

        {isModerator && winnerState?.status === "ready_to_finalize" && (
          <button onClick={handleFinalizeWinnerSelection} disabled={isSubmitting}>
            Финализировать
          </button>
        )}
      </>
    )
  }

  function renderActiveSelection() {
    if (!currentSelection || currentSelection.selection_id === null) {
      return null
    }

    const status = currentSelection.selection_status

    if (status === "nominations_open") {
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
            <div style={{ marginTop: 24 }}>
              <button onClick={handleOpenVoting} disabled={isSubmitting}>
                Завершить сбор номинаций
              </button>
            </div>
          )}
        </>
      )
    }

    if (status === "voting_open") {
      return renderVotingStage()
    }

    if (status === "voting_closed" || status === "winner_selected") {
      if (currentSelection.winner_selection_session_id === null) {
        return (
          <>
            <p>Голосование завершено.</p>

            {isModerator && (
              <button onClick={handleStartWinnerSelection} disabled={isSubmitting}>
                Начать определение победителя
              </button>
            )}
          </>
        )
      }

      return renderWinnerSteps()
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
          {currentSelection?.selection_id === null
            ? renderNoActiveSelection()
            : renderActiveSelection()}
        </>
      )}
    </Layout>
  )
}