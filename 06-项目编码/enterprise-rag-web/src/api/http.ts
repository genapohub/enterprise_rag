/** Shared HTTP client: Bearer JWT + unified {code,data,message} unwrap. */

export class ApiError extends Error {
  status: number
  code?: number

  constructor(status: number, message: string, code?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const TOKEN_KEY = 'enterprise-rag.token'

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setAccessToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export interface ApiEnvelope<T> {
  code: number
  data: T
  message: string
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
  auth?: boolean
  /** When true, send body as FormData / raw without JSON.stringify */
  rawBody?: boolean
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, auth = true, rawBody = false, headers: extraHeaders, ...rest } = options
  const headers = new Headers(extraHeaders || {})

  if (!rawBody && body !== undefined && !(body instanceof FormData)) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  }

  if (auth) {
    const token = getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  let payload: BodyInit | undefined
  if (body instanceof FormData || rawBody) {
    payload = body as BodyInit
  } else if (body !== undefined) {
    payload = JSON.stringify(body)
  }

  const res = await fetch(path, { ...rest, headers, body: payload })

  let envelope: ApiEnvelope<T> | null = null
  const text = await res.text()
  if (text) {
    try {
      envelope = JSON.parse(text) as ApiEnvelope<T>
    } catch {
      throw new ApiError(res.status, text || res.statusText || '响应解析失败')
    }
  }

  if (!envelope) {
    throw new ApiError(res.status, res.statusText || '空响应')
  }

  if (envelope.code !== 0) {
    const httpStatus =
      envelope.code === 40101 ? 401 :
      envelope.code === 40301 ? 403 :
      envelope.code === 40401 ? 404 :
      envelope.code === 40901 ? 409 :
      envelope.code === 42901 ? 429 :
      envelope.code === 40001 ? 400 :
      res.status || 500
    throw new ApiError(httpStatus, envelope.message || '请求失败', envelope.code)
  }

  return envelope.data
}

export async function requestForm<T>(path: string, form: FormData, method: string = 'POST'): Promise<T> {
  return request<T>(path, { method, body: form, rawBody: true })
}
