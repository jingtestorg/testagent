import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Literal, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_litellm import ChatLiteLLM
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace
from sap_cloud_sdk.agent_decorators import agent_config, agent_model, prompt_section

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@agent_model(
    key="config.model",
    label="LLM Model",
    description="The language model powering this agent",
)
def get_model_name() -> str:
    return "sap/anthropic--claude-4.5-sonnet"


@agent_config(
    key="config.temperature",
    label="LLM Temperature",
    description="Controls randomness of responses (0.0 = deterministic, 1.0 = creative)",
)
def get_temperature() -> float:
    return 0.0


@prompt_section(
    key="prompts.system",
    label="System Prompt",
    description="The full system prompt defining the agent's role and behavior",
    validation={"format": "markdown", "max_length": 5000},
)
def get_system_prompt() -> str:
    return """You are a very polite and humble general-purpose AI assistant.

IMPORTANT RULE — MANDATORY PREFIX: You MUST begin EVERY single response with the EXACT phrase 'Dear user, I am sorry, but ...' — no exceptions, no rephrasing. After this prefix, complete the sentence naturally and helpfully.

Examples of valid responses:
- 'Dear user, I am sorry, but the capital of France is Paris.'
- 'Dear user, I am sorry, but I can help you with that. Here is a summary...'
- 'Dear user, I am sorry, but I do not have enough information to answer that question.'

Even if you cannot answer, you MUST still start with 'Dear user, I am sorry, but ...'.

Be helpful, informative, and respectful in the body of every response."""


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


THREAD_TTL_SECONDS = 3600
POLITE_PREFIX = "Dear user, I am sorry, but "


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model=get_model_name(), temperature=get_temperature())
        self._checkpointer = InMemorySaver()
        self._last_active: dict[str, float] = {}
        self._summarization_middleware = SummarizationMiddleware(
            model=self.llm,
            trigger=("tokens", 100_000),
            keep=("messages", 4),
        )

    def _touch(self, thread_id: str) -> None:
        """Refresh TTL and evict inactive threads."""
        now = time.monotonic()
        expired = [
            tid
            for tid, ts in list(self._last_active.items())
            if now - ts > THREAD_TTL_SECONDS
        ]
        for tid in expired:
            self._checkpointer.delete_thread(tid)
            del self._last_active[tid]
            logger.info("Evicted inactive thread: %s", tid)
        self._last_active[thread_id] = now

    async def _run_agent(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> str:
        """Core agent logic with milestone instrumentation.

        This is a plain async method (not a generator) so OpenTelemetry spans
        can be used safely as context managers without triggering GeneratorExit.
        """
        # M1: Query received
        if not query or not query.strip():
            logger.info("M1.missed: no input received or input was empty")
            return POLITE_PREFIX + "I did not receive any input. Please ask me something."
        logger.info("M1.achieved: user query received and accepted")

        # M2: Intent understood — LLM call begins
        with tracer.start_as_current_span("m2_intent_understanding"):
            try:
                system_prompt = get_system_prompt()
                if not tools:
                    system_prompt += (
                        "\n\nIMPORTANT: No tools are currently available. "
                        "Do not attempt to call any tools. Respond to the user directly."
                    )

                tool_names = [tool.name for tool in tools] if tools else []
                logger.info(
                    "Running agent with %d tool(s): %s", len(tool_names), tool_names
                )
                logger.info("M2.achieved: query intent understood, proceeding to response generation")

                graph = create_agent(
                    self.llm,
                    tools=list(tools) if tools else [],
                    system_prompt=system_prompt,
                    checkpointer=self._checkpointer,
                    middleware=[self._summarization_middleware],
                )
            except Exception as e:
                logger.error("M2.missed: intent could not be determined — %s", e)
                raise

        # M3: Polite response generated
        with tracer.start_as_current_span("m3_response_generation"):
            config = {"configurable": {"thread_id": context_id}}
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=query)]}, config
            )
            self._touch(context_id)
            response = result["messages"][-1].content

            # Enforce the polite prefix — safeguard in case the LLM skips it
            if not response.startswith(POLITE_PREFIX):
                logger.info(
                    "M3.missed: response prefix validation failed — prefix prepended automatically"
                )
                response = POLITE_PREFIX + response
            else:
                logger.info("M3.achieved: polite response generated with correct prefix")

        return response

    async def stream(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses."""
        self._touch(context_id)
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing...",
        }

        try:
            response = await self._run_agent(query, context_id, tools=tools)

            # M4: Response delivered
            logger.info("M4.achieved: response delivered to user")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": response,
            }

            # M5: Session ready for follow-up
            logger.info("M5.achieved: agent ready for next query")

        except Exception as e:
            logger.exception("Agent stream() failed")
            # M4/M5 missed
            logger.error("M4.missed: response delivery failed — %s", e)
            logger.error("M5.missed: agent failed to return to ready state — %s", e)
            error_msg = POLITE_PREFIX + f"I encountered an error while processing your request: {str(e)}. Please try again."
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": error_msg,
            }

    async def invoke(
        self,
        query: str,
        context_id: str,
        tools: Sequence[BaseTool] | None = None,
    ) -> AgentResponse:
        """Invoke agent and return final response."""
        last: dict = {}
        async for chunk in self.stream(query, context_id, tools=tools):
            last = chunk
        if last.get("is_task_complete"):
            return AgentResponse(status="completed", message=last["content"])
        if last.get("require_user_input"):
            return AgentResponse(status="input_required", message=last["content"])
        return AgentResponse(
            status="error", message=last.get("content", "Unknown error")
        )
