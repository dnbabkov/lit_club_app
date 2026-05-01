import type { BookSelectionStatus, WinnerSelectionStateRead } from "../../types/selections"

type SelectionModeratorActionsProps = {
  selectionStatus: BookSelectionStatus | null
  hasWinnerSession: boolean
  winnerStateStatus: WinnerSelectionStateRead["status"] | null
  isSubmitting: boolean
  onOpenVoting: () => Promise<void> | void
  onCloseVoting: () => Promise<void> | void
  onStartWinnerSelection: () => Promise<void> | void
  onAdvanceWinnerSelection: () => Promise<void> | void
  onFinalizeWinnerSelection: () => Promise<void> | void
}

export function SelectionModeratorActions({
  selectionStatus,
  hasWinnerSession,
  winnerStateStatus,
  isSubmitting,
  onOpenVoting,
  onCloseVoting,
  onStartWinnerSelection,
  onAdvanceWinnerSelection,
  onFinalizeWinnerSelection,
}: SelectionModeratorActionsProps) {
  return (
    <div style={{ marginTop: 24 }}>
      {selectionStatus === "nominations_open" && (
        <button onClick={onOpenVoting} disabled={isSubmitting}>
          Завершить сбор номинаций
        </button>
      )}

      {selectionStatus === "voting_open" && (
        <button onClick={onCloseVoting} disabled={isSubmitting}>
          Завершить голосование
        </button>
      )}

      {(selectionStatus === "voting_closed" || selectionStatus === "winner_selected") &&
        !hasWinnerSession && (
          <button onClick={onStartWinnerSelection} disabled={isSubmitting}>
            Начать определение победителя
          </button>
        )}

      {winnerStateStatus === "in_progress" && (
        <button onClick={onAdvanceWinnerSelection} disabled={isSubmitting}>
          Следующий шаг
        </button>
      )}

      {winnerStateStatus === "ready_to_finalize" && (
        <button onClick={onFinalizeWinnerSelection} disabled={isSubmitting}>
          Финализировать
        </button>
      )}
    </div>
  )
}