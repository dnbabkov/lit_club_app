import type { SyntheticEvent } from "react"
import type { NominationRead, VoteCountRead } from "../../types/selections"
import {formatVotes} from "../../utils/pluralize.ts";

type VotingPanelProps = {
  nominations: NominationRead[]
  voteCounts: VoteCountRead[]
  selectedNominationIds: number[]
  userHasVoted: boolean
  isEditingVote: boolean
  isSubmitting: boolean
  onToggleNomination: (nominationId: number) => void
  onSubmit: (event: SyntheticEvent<HTMLFormElement>) => Promise<void> | void
  onStartEditing: () => void
}

export function VotingPanel({
  nominations,
  voteCounts,
  selectedNominationIds,
  userHasVoted,
  isEditingVote,
  isSubmitting,
  onToggleNomination,
  onSubmit,
  onStartEditing,
}: VotingPanelProps) {
  const countByNominationId = new Map(
    voteCounts.map((item) => [item.nomination_id, item.vote_count])
  )

  const canEditChoices = !userHasVoted || isEditingVote

  return (
    <>
      <p>Сейчас идёт голосование.</p>

      {userHasVoted && !isEditingVote && (
        <p>Ваш голос уже сохранён. Вы можете изменить свой выбор.</p>
      )}

      <form onSubmit={onSubmit}>
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
                {canEditChoices && (
                  <input
                    type="checkbox"
                    checked={selectedNominationIds.includes(nomination.id)}
                    onChange={() => onToggleNomination(nomination.id)}
                  />
                )}

                <div>
                  <div>
                    <strong>{nomination.title}</strong> — {nomination.author}
                  </div>
                  <div style={{ fontSize: 14, color: "#555" }}>
                    {formatVotes(countByNominationId.get(nomination.id) ?? 0)}
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

        {userHasVoted && !isEditingVote && (
          <button type="button" onClick={onStartEditing} disabled={isSubmitting}>
            Изменить выбор
          </button>
        )}

        {userHasVoted && isEditingVote && (
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Отправляем..." : "Подтвердить новый выбор"}
          </button>
        )}
      </form>
    </>
  )
}