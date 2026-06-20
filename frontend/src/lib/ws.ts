import type * as T from './types'

export class WebSocketConnection {
  private ws: WebSocket | null = null
  private url: string
  private reconnectDelay = 1000
  private maxReconnectDelay = 30000
  private reconnecting = false
  private messageHandlers: ((msg: T.WSMessage) => void)[] = []
  private connectionHandlers: ((connected: boolean) => void)[] = []

  constructor(url: string) {
    this.url = url
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          this.reconnectDelay = 1000
          this.reconnecting = false
          this.connectionHandlers.forEach((h) => h(true))
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const msg: T.WSMessage = JSON.parse(event.data)
            this.messageHandlers.forEach((h) => h(msg))
          } catch (e) {
            console.error('WS message parse error:', e)
          }
        }

        this.ws.onerror = (event) => {
          console.error('WS error:', event)
          reject(new Error('WebSocket error'))
        }

        this.ws.onclose = () => {
          this.connectionHandlers.forEach((h) => h(false))
          if (!this.reconnecting) {
            this.reconnect()
          }
        }
      } catch (e) {
        reject(e)
      }
    })
  }

  private reconnect() {
    this.reconnecting = true
    const delay = Math.min(this.reconnectDelay, this.maxReconnectDelay)
    console.log(`WS reconnecting in ${delay}ms...`)
    setTimeout(() => {
      this.connect().catch(() => {
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay)
        this.reconnect()
      })
    }, delay)
  }

  onMessage(handler: (msg: T.WSMessage) => void) {
    this.messageHandlers.push(handler)
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler)
    }
  }

  onConnectionChange(handler: (connected: boolean) => void) {
    this.connectionHandlers.push(handler)
    return () => {
      this.connectionHandlers = this.connectionHandlers.filter((h) => h !== handler)
    }
  }

  disconnect() {
    this.reconnecting = true
    this.ws?.close()
    this.ws = null
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
