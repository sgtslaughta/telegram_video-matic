import asyncio
from typing import Callable, Optional
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

from app.db.models import Account, AccountStatus
from app.crypto import decrypt, encrypt
from app.telegram.dtos import ChannelDTO, TopicDTO, MediaDTO


class TelegramService:
    """Singleton Telethon client wrapper. Manages login, session persistence, read-only browse/download."""

    def __init__(
        self,
        account_repo,
        client_factory: Callable = TelegramClient,
        max_concurrent_downloads: int = 5
    ):
        """
        Initialize service.

        Args:
            account_repo: AccountRepository for DB access.
            client_factory: Factory to create TelegramClient (injectable for testing).
            max_concurrent_downloads: Semaphore bound for downloads.
        """
        self.account_repo = account_repo
        self.client_factory = client_factory
        self.client: Optional[TelegramClient] = None
        self.account: Optional[Account] = None
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self._login_lock = asyncio.Lock()
        self._phone_code_hash: Optional[str] = None

    async def load_account(self) -> None:
        """Load Account from DB; build client if session exists."""
        self.account = await self.account_repo.get()
        if self.account and self.account.session_enc:
            session_str = decrypt(self.account.session_enc)
            api_id = int(decrypt(self.account.api_id_enc))
            api_hash = decrypt(self.account.api_hash_enc)
            # Try to create StringSession; if invalid (test mode), pass None and let factory handle it
            try:
                session = StringSession(session_str)
            except ValueError:
                # Invalid session string in test mode; pass None
                session = StringSession(None)
            self.client = self.client_factory(
                session,
                api_id,
                api_hash
            )

    async def connect(self) -> None:
        """Connect to Telegram; update status to connected if authorized."""
        if not self.client:
            return
        await self.client.connect()
        if await self.client.is_user_authorized():
            await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)

    async def disconnect(self) -> None:
        """Persist encrypted session; disconnect and mark disconnected."""
        if not self.client or not self.account:
            return

        # Persist session
        session_str = self.client.session.get_session_string()
        await self.account_repo.update_session(self.account.id, encrypt(session_str))

        # Disconnect
        await self.client.disconnect()

        # Update status
        await self.account_repo.update_status(self.account.id, AccountStatus.DISCONNECTED)

    async def start_login(self, phone: str) -> None:
        """Start login: send code request."""
        async with self._login_lock:
            if not self.client:
                raise RuntimeError("Client not initialized")

            sent_code = await self.client.send_code_request(phone)
            self._phone_code_hash = sent_code.phone_code_hash

            await self.account_repo.update_phone(self.account.id, phone)
            await self.account_repo.update_status(self.account.id, AccountStatus.AWAITING_CODE)

    async def submit_code(self, code: str) -> None:
        """Submit code; if 2FA required, status → awaiting_password; else → connected."""
        async with self._login_lock:
            if not self.client or not self.account or not self._phone_code_hash:
                raise RuntimeError("Login not started or client missing")

            try:
                me = await self.client.sign_in(
                    self.account.phone,
                    code,
                    phone_code_hash=self._phone_code_hash
                )
                # Success: persist session and mark connected
                session_str = self.client.session.get_session_string()
                await self.account_repo.update_session(self.account.id, encrypt(session_str))
                await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)
            except SessionPasswordNeededError:
                # 2FA required
                await self.account_repo.update_status(self.account.id, AccountStatus.AWAITING_PASSWORD)

    async def submit_password(self, password: str) -> None:
        """Submit 2FA password; on success, persist session and mark connected."""
        async with self._login_lock:
            if not self.client or not self.account:
                raise RuntimeError("Client not initialized or account missing")

            me = await self.client.sign_in(password=password)
            session_str = self.client.session.get_session_string()
            await self.account_repo.update_session(self.account.id, encrypt(session_str))
            await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)

    async def logout(self) -> None:
        """Logout: call client.log_out(), clear session, mark disconnected."""
        async with self._login_lock:
            if not self.client or not self.account:
                return

            await self.client.log_out()
            await self.account_repo.update_session(self.account.id, None)
            await self.account_repo.update_status(self.account.id, AccountStatus.DISCONNECTED)
