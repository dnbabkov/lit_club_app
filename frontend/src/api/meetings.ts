import { get, patch, post } from "./http"
import type {
  MeetingCreatePayload,
  MeetingRead,
  MeetingScheduleUpdatePayload,
  MeetingWithSelectionRead,
} from "../types/meetings"

export async function getMeetings(): Promise<MeetingRead[]> {
  return get<MeetingRead[]>("/meetings/")
}

export async function getLatestMeeting(): Promise<MeetingRead> {
  return get<MeetingRead>("/meetings/latest")
}

export async function getMeetingById(meetingId: number): Promise<MeetingRead> {
  return get<MeetingRead>(`/meetings/${meetingId}`)
}

export async function getMeetingsByYear(year: number): Promise<MeetingRead[]> {
  return get<MeetingRead[]>(`/meetings/year/${year}`)
}

export async function createMeeting(
  payload: MeetingCreatePayload
): Promise<MeetingRead> {
  return post<MeetingRead>("/meetings/", payload)
}

export async function scheduleMeeting(
  meetingId: number,
  payload: MeetingScheduleUpdatePayload
): Promise<MeetingRead> {
  return patch<MeetingRead>(`/meetings/${meetingId}/schedule`, payload)
}

export async function finishMeeting(meetingId: number): Promise<MeetingRead> {
  return post<MeetingRead>(`/meetings/${meetingId}/finish`)
}

export async function startNextMeeting(): Promise<MeetingWithSelectionRead> {
  return post<MeetingWithSelectionRead>("/meetings/start-next")
}