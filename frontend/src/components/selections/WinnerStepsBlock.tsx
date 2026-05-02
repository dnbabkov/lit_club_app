import type { NominationRead, WinnerSelectionStateRead } from "../../types/selections"
import {formatVotes} from "../../utils/pluralize.ts";

type WinnerStepsBlockProps = {
  winnerState: WinnerSelectionStateRead | null
  nominations: NominationRead[]
}

export function WinnerStepsBlock({
  winnerState,
  nominations,
}: WinnerStepsBlockProps) {
  const nominationTitleById = new Map(
    nominations.map((nomination) => [nomination.id, nomination.title])
  )

  function getNominationTitle(nominationId: number): string {
    return nominationTitleById.get(nominationId) ?? `Номинация #${nominationId}`
  }

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
                    {getNominationTitle(candidate.nomination_id)}:{" "}
                    {formatVotes(candidate.vote_count)}, шанс вылета{" "}
                    {(candidate.elimination_probability * 100).toFixed(1)}%
                    {candidate.was_eliminated ? " — выбыла" : ""}
                  </li>
                ))}
              </ul>

              <p>
                Вылетел кандидат:{" "}
                <strong>{getNominationTitle(step.eliminated_nomination_id)}</strong>
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p>Шагов пока нет.</p>
      )}

      {winnerState?.winner_nomination_id && (
        <p>
          Победившая номинация:{" "}
          <strong>{getNominationTitle(winnerState.winner_nomination_id)}</strong>
        </p>
      )}
    </>
  )
}