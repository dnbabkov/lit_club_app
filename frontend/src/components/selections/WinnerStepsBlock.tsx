import type { WinnerSelectionStateRead } from "../../types/selections"

type WinnerStepsBlockProps = {
  winnerState: WinnerSelectionStateRead | null
}

export function WinnerStepsBlock({ winnerState }: WinnerStepsBlockProps) {
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
                    Номинация #{candidate.nomination_id}: {candidate.vote_count} голосов, шанс
                    вылета {(candidate.elimination_probability * 100).toFixed(1)}%
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
    </>
  )
}