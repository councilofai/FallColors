"""Test orchestrator for managing chatbot testing sessions."""

import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

from app.services.browser_service import BrowserService
from app.services.llm_service import LLMService
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TestOrchestrator:
    """Orchestrates the entire chatbot testing process."""

    def __init__(
        self,
        session_id: str,
        url: str,
        topic: str,
        max_rounds: int,
        adversarial_intensity: int,
        input_selector: Optional[str] = None,
        submit_selector: Optional[str] = None,
        headless: bool = False,
        event_callback: Optional[Callable] = None
    ):
        """
        Initialize test orchestrator.

        Args:
            session_id: Unique session identifier
            url: Target chatbot URL
            topic: Conversation topic
            max_rounds: Maximum number of conversation rounds
            adversarial_intensity: Adversarial intensity level (1-10)
            input_selector: CSS selector for chat input
            submit_selector: CSS selector for submit button
            headless: Whether to run browser in headless mode
            event_callback: Async callback for sending events
        """
        self.session_id = session_id
        self.url = url
        self.topic = topic
        self.max_rounds = max_rounds
        self.adversarial_intensity = adversarial_intensity
        self.input_selector = input_selector
        self.submit_selector = submit_selector
        self.headless = headless
        self.event_callback = event_callback

        self.browser_service = BrowserService(headless=headless)
        self.llm_service = LLMService()

        self.conversation_history = []
        self.safety_evaluations = []
        self.screenshots = []
        self.status = "pending"
        self.error_message = None

    async def send_event(self, event_type: str, data: Dict):
        """Send an event through the callback if available."""
        if self.event_callback:
            try:
                await self.event_callback({
                    "type": event_type,
                    "session_id": self.session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                })
            except Exception as e:
                logger.error(f"Error sending event: {e}")

    async def run(self) -> Dict:
        """
        Run the complete testing session.

        Returns:
            Dictionary containing test results
        """
        try:
            self.status = "running"
            await self.send_event("test_started", {
                "url": self.url,
                "topic": self.topic,
                "max_rounds": self.max_rounds,
                "adversarial_intensity": self.adversarial_intensity
            })

            # Initialize browser
            logger.info("Starting browser...")
            await self.browser_service.start()
            await self.send_event("browser_started", {})

            # Navigate to URL
            logger.info(f"Navigating to {self.url}")
            navigation_success = await self.browser_service.navigate(self.url)

            if not navigation_success:
                raise Exception(f"Failed to navigate to {self.url}")

            await self.send_event("navigation_complete", {"url": self.url})

            # Take initial screenshot
            screenshot = await self.browser_service.take_screenshot()
            if screenshot:
                self.screenshots.append(screenshot)
                await self.send_event("screenshot", {"image": screenshot})

            # Find chat interface
            logger.info("Finding chat interface...")
            input_sel, submit_sel = await self.browser_service.find_chat_interface(
                self.input_selector,
                self.submit_selector
            )

            if not input_sel or not submit_sel:
                raise Exception("Could not find chat interface. Please provide CSS selectors.")

            self.input_selector = input_sel
            self.submit_selector = submit_sel

            await self.send_event("interface_found", {
                "input_selector": input_sel,
                "submit_selector": submit_sel
            })

            # Run conversation rounds
            for round_num in range(self.max_rounds):
                logger.info(f"Starting round {round_num + 1}/{self.max_rounds}")
                await self.send_event("round_started", {
                    "round": round_num + 1,
                    "total_rounds": self.max_rounds
                })

                # Generate test prompt
                previous_response = None
                if self.conversation_history:
                    previous_response = self.conversation_history[-1]["chatbot"]

                test_prompt = await self.llm_service.generate_test_prompt(
                    topic=self.topic,
                    round_number=round_num,
                    max_rounds=self.max_rounds,
                    adversarial_intensity=self.adversarial_intensity,
                    conversation_history=self.conversation_history,
                    previous_chatbot_response=previous_response
                )

                await self.send_event("prompt_generated", {
                    "round": round_num + 1,
                    "prompt": test_prompt
                })

                # Send message to chatbot
                logger.info(f"Sending: {test_prompt[:100]}...")
                send_success = await self.browser_service.send_message(
                    message=test_prompt,
                    input_selector=self.input_selector,
                    submit_selector=self.submit_selector
                )

                if not send_success:
                    logger.warning(f"Failed to send message in round {round_num + 1}")
                    await self.send_event("send_failed", {"round": round_num + 1})
                    continue

                await self.send_event("message_sent", {
                    "round": round_num + 1,
                    "message": test_prompt
                })

                # Wait for response
                await asyncio.sleep(3)  # Give chatbot time to respond

                # Get chatbot response
                chatbot_response = await self.browser_service.get_latest_response()

                if not chatbot_response:
                    logger.warning(f"No response received in round {round_num + 1}")
                    chatbot_response = "[No response detected]"

                logger.info(f"Received: {chatbot_response[:100]}...")
                await self.send_event("message_received", {
                    "round": round_num + 1,
                    "message": chatbot_response
                })

                # Take screenshot after exchange
                screenshot = await self.browser_service.take_screenshot()
                if screenshot:
                    self.screenshots.append(screenshot)
                    await self.send_event("screenshot", {"image": screenshot})

                # Evaluate safety
                logger.info("Evaluating safety...")
                safety_eval = await self.llm_service.evaluate_safety(
                    chatbot_response=chatbot_response,
                    test_prompt=test_prompt,
                    topic=self.topic,
                    round_number=round_num
                )

                self.safety_evaluations.append(safety_eval)
                await self.send_event("safety_evaluation", {
                    "round": round_num + 1,
                    "evaluation": safety_eval
                })

                # Store conversation
                self.conversation_history.append({
                    "round": round_num + 1,
                    "tester": test_prompt,
                    "chatbot": chatbot_response,
                    "safety_evaluation": safety_eval
                })

                await self.send_event("round_complete", {
                    "round": round_num + 1,
                    "safety_score": safety_eval.get("overall_score", 0)
                })

                # Small delay between rounds
                await asyncio.sleep(2)

            # Generate final report
            logger.info("Generating final report...")
            final_report = await self.llm_service.generate_final_report(
                conversation_history=self.conversation_history,
                safety_evaluations=self.safety_evaluations,
                topic=self.topic,
                adversarial_intensity=self.adversarial_intensity
            )

            self.status = "completed"
            results = {
                "session_id": self.session_id,
                "status": "completed",
                "conversation": self.conversation_history,
                "safety_evaluations": self.safety_evaluations,
                "report": final_report,
                "screenshots": self.screenshots,
                "metadata": {
                    "url": self.url,
                    "topic": self.topic,
                    "max_rounds": self.max_rounds,
                    "adversarial_intensity": self.adversarial_intensity,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }

            await self.send_event("test_complete", {"report": final_report})

            return results

        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.status = "failed"
            self.error_message = str(e)

            await self.send_event("test_failed", {"error": str(e)})

            return {
                "session_id": self.session_id,
                "status": "failed",
                "error": str(e),
                "conversation": self.conversation_history,
                "safety_evaluations": self.safety_evaluations,
                "screenshots": self.screenshots
            }

        finally:
            # Cleanup
            logger.info("Cleaning up browser...")
            await self.browser_service.stop()
            await self.send_event("browser_stopped", {})

    async def stop(self):
        """Stop the test session."""
        self.status = "stopped"
        await self.browser_service.stop()
