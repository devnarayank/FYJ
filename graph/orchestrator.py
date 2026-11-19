"""
LangGraph Orchestrator — the heart of the multi-agent pipeline.

Defines a state graph with 4 agent nodes connected sequentially:
  START → analyze_resume → search_and_match → execute_outreach → track_followups → END

Uses TypedDict state that flows through each node, accumulating results.
Each node calls its corresponding agent module and returns updated state.
"""
import logging
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from config.constants import DEFAULT_BOARDS
from config.settings import AppSettings, get_settings
from graph.tools import TOOL_REGISTRY as GRAPH_TOOL_REGISTRY
from llm.factory import build_llm
from models.database import Database
from tools.validators import validate_file_path

TOOL_REGISTRY = GRAPH_TOOL_REGISTRY

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# LangGraph State Definition
# ──────────────────────────────────────────────

class JobHuntState(TypedDict, total=False):
    """
    State that flows through the LangGraph pipeline.
    Each node reads from and writes to this shared state.
    """
    # ── Inputs ──
    resume_path: str
    target_roles: list[str]
    target_locations: list[str]
    boards: list[str]

    # ── Agent 1 outputs ──
    resume_text: str
    candidate_profile: dict  # Serialized CandidateProfile

    # ── Agent 2 outputs ──
    search_queries: list[str]
    matched_jobs: list[dict]  # Serialized MatchedJob list
    search_metadata: dict

    # ── Agent 3 outputs ──
    outreach_results: list[dict]
    outreach_summary: dict

    # ── Agent 4 outputs ──
    tracking_dashboard: dict

    # ── Control ──
    current_phase: str
    errors: list[str]
    messages: list


# ──────────────────────────────────────────────
# Validation Functions
# ──────────────────────────────────────────────

def _validate_state_start(state: JobHuntState) -> bool:
    """Validate initial state before pipeline starts."""
    errors = []
    
    if not state.get("resume_path"):
        errors.append("resume_path is required")
    else:
        try:
            validate_file_path(state["resume_path"])
        except ValueError as e:
            errors.append(f"Invalid resume path: {str(e)}")
    
    if errors:
        logger.error("State validation failed: " + "; ".join(errors))
        return False
    
    return True


def _validate_resume_output(state: JobHuntState) -> bool:
    """Validate resume analysis output."""
    if not state.get("resume_text"):
        logger.error("Resume text is missing")
        return False
    if not state.get("candidate_profile"):
        logger.error("Candidate profile is missing")
        return False
    return True


def _validate_matching_output(state: JobHuntState) -> bool:
    """Validate job matching output."""
    matched_jobs = state.get("matched_jobs", [])
    if not isinstance(matched_jobs, list):
        logger.error("Matched jobs must be a list")
        return False
    return True


# ──────────────────────────────────────────────
# Tool-based LangGraph Agent
# ──────────────────────────────────────────────

def node_agent(state: JobHuntState) -> dict:
    """Call the configured LLM and bind available tools for a tool-calling workflow."""
    llm = build_llm(get_settings(), task="job_hunt_agent")
    model = llm.bind_tools(TOOL_REGISTRY)

    messages = state.get("messages", [])
    if not messages:
        messages = [
            HumanMessage(
                content=(
                    f"Analyze the resume workflow for: {state.get('resume_path', 'job search')}\n"
                    f"target_roles={state.get('target_roles', [])}\n"
                    f"target_locations={state.get('target_locations', [])}"
                )
            )
        ]

    response = model.invoke(messages)
    return {"messages": messages + [response], "current_phase": "tool_calling"}


def should_use_tools(state: JobHuntState) -> str:
    """Route to the tool node only when the model asked for a tool call."""
    messages = state.get("messages", [])
    if not messages:
        return "finalize"

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    if tool_calls:
        return "tool_execution"
    return "finalize"


def build_tool_pipeline() -> StateGraph:
    """Build a proper tool-calling LangGraph workflow."""
    graph = StateGraph(JobHuntState)
    graph.add_node("agent", node_agent)
    graph.add_node("tool_execution", ToolNode(TOOL_REGISTRY))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            "tool_execution": "tool_execution",
            "finalize": END,
        },
    )
    graph.add_edge("tool_execution", "agent")
    return graph.compile()


def run_tool_pipeline(
    resume_path: str,
    target_roles: list[str] | None = None,
    target_locations: list[str] | None = None,
    boards: list[str] | None = None,
) -> dict:
    """Execute the real tool-calling graph for the resume/job workflow."""
    app = build_tool_pipeline()
    initial_state: JobHuntState = {
        "resume_path": resume_path,
        "target_roles": target_roles or [],
        "target_locations": target_locations or [],
        "boards": boards or DEFAULT_BOARDS,
        "messages": [
            HumanMessage(
                content=(
                    f"Start the job hunt workflow for resume: {resume_path}. "
                    f"Roles={target_roles or []}. Locations={target_locations or []}."
                )
            )
        ],
        "matched_jobs": [],
        "errors": [],
    }
    return app.invoke(initial_state)


# ──────────────────────────────────────────────
# Node Functions
# ──────────────────────────────────────────────

def node_analyze_resume(state: JobHuntState) -> dict:
    """Node 1: Resume Analysis Agent."""
    from agents.resume_agent import analyze_resume

    # Validate input state
    if not _validate_state_start(state):
        return {
            "current_phase": "error",
            "errors": state.get("errors", []) + ["Invalid input state for resume analysis"],
        }
    
    settings = get_settings()
    try:
        result = analyze_resume(state["resume_path"], settings)
        
        # Validate output
        if not _validate_resume_output(result):
            return {
                "current_phase": "error",
                "errors": state.get("errors", []) + ["Resume analysis produced incomplete results"],
            }
        
        return {
            "resume_text": result["resume_text"],
            "candidate_profile": result["candidate_profile"].model_dump(),
            "current_phase": "matching",
            "errors": state.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        return {
            "current_phase": "error",
            "errors": state.get("errors", []) + [f"Resume analysis: {str(e)}"],
        }


def node_search_and_match(state: JobHuntState) -> dict:
    """Node 2: Job Search & Matching Agent."""
    from agents.job_match_agent import search_and_match_jobs
    from models.schemas import CandidateProfile

    settings = get_settings()
    try:
        profile = CandidateProfile(**state["candidate_profile"])
        result = search_and_match_jobs(
            candidate_profile=profile,
            resume_text=state.get("resume_text", ""),
            settings=settings,
            target_locations=state.get("target_locations", []),
            target_roles=state.get("target_roles", []),
            boards=state.get("boards", DEFAULT_BOARDS),
        )
        return {
            "search_queries": result.get("search_queries", []),
            "matched_jobs": [j.model_dump() for j in result["matched_jobs"]],
            "search_metadata": result["search_metadata"].model_dump() if result.get("search_metadata") else {},
            "current_phase": "outreach",
            "errors": state.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Job matching failed: {e}")
        return {
            "matched_jobs": [],
            "current_phase": "outreach",
            "errors": state.get("errors", []) + [f"Job matching: {str(e)}"],
        }


def node_execute_outreach(state: JobHuntState) -> dict:
    """Node 3: Outreach Agent."""
    # Outreach implementation removed — run lightweight persistence step instead.
    from models.schemas import CandidateProfile, MatchedJob

    settings = get_settings()

    matched_jobs_data = state.get("matched_jobs", [])
    if not matched_jobs_data:
        logger.info("No matched jobs to process for outreach (agent removed).")
        return {
            "outreach_results": [],
            "outreach_summary": {"total_attempted": 0, "successfully_sent": 0, "skipped": 0, "failed": 0},
            "current_phase": "tracking",
            "errors": state.get("errors", []),
        }

    try:
        # Persist matched jobs to DB so downstream tracking can operate.
        profile = CandidateProfile(**state.get("candidate_profile", {}))
        jobs = [MatchedJob(**j) for j in matched_jobs_data]

        db = Database(settings.db_path)
        for job in jobs:
            db.insert_job(job)

        # No external outreach executed — return honest summary (FR-006)
        summary = {"total_attempted": 0, "successfully_sent": 0, "skipped": len(jobs), "failed": 0}
        return {
            "outreach_results": [],
            "outreach_summary": summary,
            "current_phase": "tracking",
            "errors": state.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Outreach persistence failed: {e}")
        return {
            "current_phase": "tracking",
            "errors": state.get("errors", []) + [f"Outreach persistence: {str(e)}"],
        }


def node_track_followups(state: JobHuntState) -> dict:
    """Node 4: Follow-up & Tracking Agent."""
    # Follow-up agent removed — synthesize a simple dashboard from DB snapshots.
    from models.schemas import CandidateProfile

    settings = get_settings()
    db = Database(settings.db_path)

    try:
        # Build a lightweight dashboard using existing DB helper methods.
        dashboard = {
            "status_breakdown": db.get_status_breakdown(),
            "recent_activity": db.get_recent_activity(limit=20),
        }
        return {
            "tracking_dashboard": dashboard,
            "current_phase": "complete",
            "errors": state.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Tracking dashboard generation failed: {e}")
        return {
            "current_phase": "complete",
            "errors": state.get("errors", []) + [f"Tracking: {str(e)}"],
        }


# ──────────────────────────────────────────────
# Conditional Edge: Skip outreach if no matches
# ──────────────────────────────────────────────

def should_do_outreach(state: JobHuntState) -> str:
    """Decide whether to proceed with outreach or skip to tracking."""
    matched = state.get("matched_jobs", [])
    if matched:
        return "execute_outreach"
    else:
        logger.info("No matched jobs found. Skipping outreach → tracking.")
        return "track_followups"


# ──────────────────────────────────────────────
# Graph Assembly
# ──────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """
    Build and compile the LangGraph pipeline.

    Graph structure:
        START → analyze_resume → search_and_match → [conditional]
            → execute_outreach → track_followups → END
            → track_followups → END (if no matches)

    Note: the main workflow is not a tool-calling graph. A ToolNode is only used
    by a separate experimental utility graph and should not be inserted between
    the real agent stages, because the state produced by the agent nodes does not
    include a valid LangChain message payload for ToolNode parsing.
    """
    graph = StateGraph(JobHuntState)

    # Add nodes
    graph.add_node("analyze_resume", node_analyze_resume)
    graph.add_node("search_and_match", node_search_and_match)
    graph.add_node("execute_outreach", node_execute_outreach)
    graph.add_node("track_followups", node_track_followups)

    # Add edges
    graph.add_edge(START, "analyze_resume")
    graph.add_edge("analyze_resume", "search_and_match")

    # Conditional: skip outreach if no matches
    graph.add_conditional_edges(
        "search_and_match",
        should_do_outreach,
        {
            "execute_outreach": "execute_outreach",
            "track_followups": "track_followups",
        },
    )

    graph.add_edge("execute_outreach", "track_followups")
    graph.add_edge("track_followups", END)

    return graph.compile()


def run_pipeline(
    resume_path: str,
    target_roles: list[str] | None = None,
    target_locations: list[str] | None = None,
    boards: list[str] | None = None,
) -> dict:
    """
    Execute the full LangGraph pipeline.
    Returns the final state dict.
    """
    app = build_pipeline()

    initial_state: JobHuntState = {
        "resume_path": resume_path,
        "target_roles": target_roles or [],
        "target_locations": target_locations or [],
        "boards": boards or DEFAULT_BOARDS,
        "resume_text": "",
        "candidate_profile": {},
        "search_queries": [],
        "matched_jobs": [],
        "search_metadata": {},
        "outreach_results": [],
        "outreach_summary": {},
        "tracking_dashboard": {},
        "current_phase": "init",
        "errors": [],
    }

    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  Multi-Agent Job Hunter — Pipeline Start  ║")
    logger.info("╚══════════════════════════════════════════╝")

    final_state = app.invoke(initial_state)

    errors = final_state.get("errors", [])
    if errors:
        logger.warning(f"Pipeline completed with {len(errors)} error(s):")
        for err in errors:
            logger.warning(f"  • {err}")
    else:
        logger.info("Pipeline completed successfully!")

    return final_state
