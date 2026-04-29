const API_URL = import.meta.env.VITE_API_URL

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE"

type RequestOptions = {
    method?: HttpMethod
    body?: unknown
    token?: string | null
}

export class ApiError extends Error {
    status: number
    constructor(status: number, message: string) {
        super(message);
        this.status = status
        this.name = "ApiError"
    }
}

import { getToken } from "../auth/token"

async function request<T>(
    path: string,
    options: RequestOptions = {}
): Promise<T> {
    const method = options.method ?? "GET"
    const token = options.token ?? getToken()

    const headers: Record<string, string> = {}

    if (options.body !== undefined) {
        headers["Content-Type"] = "application/json"
    }
    if (token) {
        headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${path}`, {
        method,
        headers,
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })

    if (!response.ok) {
        let errorMessage = "Request failed"

        try {
            const errorData = await response.json()
            if (errorData.detail) {
                errorMessage = errorData.detail
            }
        } catch {
            errorMessage = "No JSON"
        }

        throw new ApiError(response.status, errorMessage)
    }

    if (response.status === 204) {
        return null as T
    }

    const data = await response.json()
    return data as T
}

export async function get<T>(path: string): Promise<T> {
    return request<T>(path, {method : "GET"})
}

export async function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body })
}

export async function patch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body })
}

export async function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" })
}