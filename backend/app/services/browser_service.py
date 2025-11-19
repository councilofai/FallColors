"""Browser automation service for interacting with chatbots."""

import asyncio
import base64
from typing import Optional, Dict, Tuple
from playwright.async_api import async_playwright, Browser, Page, Playwright
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class BrowserService:
    """Service for automated browser interaction with chatbots."""

    def __init__(self, headless: bool = False):
        """Initialize browser service."""
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self):
        """Start the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1280, "height": 720})

    async def stop(self):
        """Stop the browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str) -> bool:
        """
        Navigate to a URL.

        Args:
            url: The URL to navigate to

        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            response = await self.page.goto(url, wait_until="networkidle", timeout=30000)
            return response.status < 400
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def find_chat_interface(
        self,
        input_selector: Optional[str] = None,
        submit_selector: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the chat input and submit button on the page.

        Args:
            input_selector: Optional CSS selector for input field
            submit_selector: Optional CSS selector for submit button

        Returns:
            Tuple of (input_selector, submit_selector) if found
        """
        # If selectors provided, validate them
        if input_selector and submit_selector:
            try:
                input_exists = await self.page.locator(input_selector).count() > 0
                submit_exists = await self.page.locator(submit_selector).count() > 0

                if input_exists and submit_exists:
                    return (input_selector, submit_selector)
            except Exception as e:
                logger.warning(f"Provided selectors invalid: {e}")

        # Auto-detect chat interface
        logger.info("Auto-detecting chat interface...")

        # Common input field patterns
        input_patterns = [
            'input[type="text"]',
            'textarea',
            'input[placeholder*="message" i]',
            'input[placeholder*="chat" i]',
            'input[placeholder*="type" i]',
            'textarea[placeholder*="message" i]',
            'textarea[placeholder*="chat" i]',
            '[contenteditable="true"]',
            'input[name*="message" i]',
            'textarea[name*="message" i]',
            '#chat-input',
            '#message-input',
            '.chat-input',
            '.message-input'
        ]

        # Common submit button patterns
        submit_patterns = [
            'button[type="submit"]',
            'button:has-text("Send")',
            'button:has-text("Submit")',
            'button:has-text(">")',
            'button[aria-label*="send" i]',
            'button[aria-label*="submit" i]',
            '[role="button"]:has-text("Send")',
            '#send-button',
            '#submit-button',
            '.send-button',
            '.submit-button'
        ]

        found_input = None
        found_submit = None

        # Try to find input field
        for pattern in input_patterns:
            try:
                count = await self.page.locator(pattern).count()
                if count > 0:
                    # If multiple matches, try to find the most visible one
                    for i in range(count):
                        element = self.page.locator(pattern).nth(i)
                        if await element.is_visible():
                            found_input = pattern
                            if count > 1:
                                found_input = f"{pattern} >> nth={i}"
                            break
                    if found_input:
                        break
            except Exception:
                continue

        # Try to find submit button
        for pattern in submit_patterns:
            try:
                count = await self.page.locator(pattern).count()
                if count > 0:
                    for i in range(count):
                        element = self.page.locator(pattern).nth(i)
                        if await element.is_visible():
                            found_submit = pattern
                            if count > 1:
                                found_submit = f"{pattern} >> nth={i}"
                            break
                    if found_submit:
                        break
            except Exception:
                continue

        if found_input and found_submit:
            logger.info(f"Auto-detected: input={found_input}, submit={found_submit}")
            return (found_input, found_submit)

        logger.warning("Could not auto-detect chat interface")
        return (None, None)

    async def send_message(
        self,
        message: str,
        input_selector: str,
        submit_selector: str,
        wait_for_response: bool = True,
        timeout: int = 30000
    ) -> bool:
        """
        Send a message to the chatbot.

        Args:
            message: The message to send
            input_selector: CSS selector for input field
            submit_selector: CSS selector for submit button
            wait_for_response: Whether to wait for a response
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if message was sent successfully
        """
        try:
            # Clear and fill input
            input_field = self.page.locator(input_selector)
            await input_field.clear()
            await input_field.fill(message)

            # Small delay to simulate human typing
            await asyncio.sleep(0.5)

            # Click submit button
            submit_button = self.page.locator(submit_selector)
            await submit_button.click()

            # Wait for potential response
            if wait_for_response:
                await asyncio.sleep(2)  # Wait for response to appear

            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def get_latest_response(
        self,
        previous_content: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the latest chatbot response.

        Args:
            previous_content: Previous page content to diff against

        Returns:
            The latest response text, or None if not found
        """
        try:
            # Get all message elements - try common patterns
            message_patterns = [
                '[class*="message"]',
                '[class*="chat"]',
                '[role="log"]',
                '[class*="response"]',
                '[class*="assistant"]',
                '[class*="bot"]'
            ]

            for pattern in message_patterns:
                try:
                    messages = await self.page.locator(pattern).all()
                    if messages:
                        # Get the last message
                        last_message = messages[-1]
                        text = await last_message.text_content()
                        if text and text.strip():
                            return text.strip()
                except Exception:
                    continue

            # Fallback: get all visible text and extract new content
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            if lines:
                # Return last non-empty line as potential response
                return lines[-1]

            return None

        except Exception as e:
            logger.error(f"Failed to get response: {e}")
            return None

    async def take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot of the current page.

        Returns:
            Base64 encoded screenshot, or None if failed
        """
        try:
            screenshot_bytes = await self.page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return screenshot_b64
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    async def wait_for_element(
        self,
        selector: str,
        timeout: int = 10000
    ) -> bool:
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector to wait for
            timeout: Maximum time to wait in milliseconds

        Returns:
            True if element appeared, False otherwise
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_page_info(self) -> Dict[str, str]:
        """
        Get information about the current page.

        Returns:
            Dictionary with page title, URL, etc.
        """
        try:
            return {
                "url": self.page.url,
                "title": await self.page.title(),
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {"url": "", "title": ""}
