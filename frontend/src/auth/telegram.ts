type TelegramWebApp = {
  initData: string
  ready: () => void
  expand: () => void
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp }
  }
}

export function getTelegramApp(): TelegramWebApp | undefined {
  return window.Telegram?.WebApp
}
