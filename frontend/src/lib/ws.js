export class WebSocketConnection {
    constructor(url) {
        Object.defineProperty(this, "ws", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "url", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "reconnectDelay", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 1000
        });
        Object.defineProperty(this, "maxReconnectDelay", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 30000
        });
        Object.defineProperty(this, "reconnecting", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: false
        });
        Object.defineProperty(this, "messageHandlers", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        Object.defineProperty(this, "connectionHandlers", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        this.url = url;
    }
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);
                this.ws.onopen = () => {
                    this.reconnectDelay = 1000;
                    this.reconnecting = false;
                    this.connectionHandlers.forEach((h) => h(true));
                    resolve();
                };
                this.ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        this.messageHandlers.forEach((h) => h(msg));
                    }
                    catch (e) {
                        console.error('WS message parse error:', e);
                    }
                };
                this.ws.onerror = (event) => {
                    console.error('WS error:', event);
                    reject(new Error('WebSocket error'));
                };
                this.ws.onclose = () => {
                    this.connectionHandlers.forEach((h) => h(false));
                    if (!this.reconnecting) {
                        this.reconnect();
                    }
                };
            }
            catch (e) {
                reject(e);
            }
        });
    }
    reconnect() {
        this.reconnecting = true;
        const delay = Math.min(this.reconnectDelay, this.maxReconnectDelay);
        console.log(`WS reconnecting in ${delay}ms...`);
        setTimeout(() => {
            this.connect().catch(() => {
                this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
                this.reconnect();
            });
        }, delay);
    }
    onMessage(handler) {
        this.messageHandlers.push(handler);
        return () => {
            this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
        };
    }
    onConnectionChange(handler) {
        this.connectionHandlers.push(handler);
        return () => {
            this.connectionHandlers = this.connectionHandlers.filter((h) => h !== handler);
        };
    }
    disconnect() {
        this.reconnecting = true;
        this.ws?.close();
        this.ws = null;
    }
    isConnected() {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}
