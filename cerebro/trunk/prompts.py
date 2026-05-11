"""Prompt templates for planner, critic, and RAG-augmented direct mode.

Templates are plain f-string-like constants. No Jinja2 in Phase 0 to keep
the dependency surface small.
"""

from __future__ import annotations

# Direct mode (DIRECT and RAG share the user-turn shape; RAG just prepends
# retrieved context).
DIRECT_SYSTEM_PROMPT = (
    "You are a careful, concise assistant. Answer the user's question "
    "directly. If you do not know, say so."
)

RAG_CONTEXT_PREAMBLE = (
    "The following retrieved passages may be relevant. Use them if they help, "
    "otherwise ignore. Do not invent facts that are not in the passages."
)

# Planner mode: produces a short numbered plan, not the answer itself.
PLANNER_SYSTEM_PROMPT = (
    "You are a planner. Given the user's question, output a short numbered "
    "plan (3-6 steps) describing how to answer. Do NOT answer yet."
)

# Solver mode: receives the plan + original query and produces the answer.
SOLVER_SYSTEM_PROMPT = (
    "You are a solver. You will receive a plan and the original question. "
    "Follow the plan and produce the final answer. Be concise."
)

# Critic: judges an answer against the original query, returning either
# APPROVE or a short revision suggestion. Used by PLANNER_SOLVE_CRITIC.
CRITIC_SYSTEM_PROMPT = (
    "You are a critic. You will receive a question and a candidate answer. "
    "If the answer is correct, complete, and faithful, reply with exactly "
    "'APPROVE'. Otherwise reply with 'REVISE: ' followed by a one-sentence "
    "description of what must change."
)
