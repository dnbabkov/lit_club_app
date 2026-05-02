export function formatVotes(count: number): string {
  const absCount = Math.abs(count)
  const lastTwo = absCount % 100
  const lastOne = absCount % 10

  if (lastTwo >= 11 && lastTwo <= 14) {
    return `${count} голосов`
  }

  if (lastOne === 1) {
    return `${count} голос`
  }

  if (lastOne >= 2 && lastOne <= 4) {
    return `${count} голоса`
  }

  return `${count} голосов`
}