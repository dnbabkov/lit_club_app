import type {CurrentSelectionRead} from "../../types/selections.ts";

type SelectionStatusBlockProps = {
    currentSelection: CurrentSelectionRead | null
}

export function SelectionStatusBlock({
    currentSelection,
}: SelectionStatusBlockProps) {
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