"""Small online Q-learning policy for Bitey conversation strategy.

The policy does not replace the language model. It learns which conversational
strategy is most useful for a given context and feeds that strategy back into
the existing Bitey decision engine.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import random
from datetime import datetime, timezone
from typing import Any
from app.database.supabase import database

ACTIONS = ("answer_direct", "use_context", "ask_clarification", "investigate")

ALPHA = float(os.getenv("BITEY_Q_ALPHA", "0.20"))
GAMMA = float(os.getenv("BITEY_Q_GAMMA", "0.85"))
EPSILON = float(os.getenv("BITEY_Q_EPSILON", "0.05"))


def _state_key(context: dict[str, Any]) -> str:
    state = {
        "channel": context.get("channel"),
        "has_history": bool(context.get("has_history")),
        "follow_up": bool(context.get("is_follow_up")),
        "pending": bool(context.get("pending_question")),
        "problem": bool(context.get("active_problem")),
        "goal": bool(context.get("active_goal")),
        "confidence": round(float(context.get("confidence") or 0), 1),
        "message_class": context.get("message_class", "unknown"),
        # Q-learning is conditioned on the already-interpreted turn, never used to infer intent.
        "interpreted_intent": context.get("interpreted_intent"),
        "intent_corrected": bool(context.get("intent_corrected")),
    }
    raw = json.dumps(state, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _rows(company_id: int, state_key: str) -> list[dict[str, Any]]:
    try:
        result = database.table("bitey_q_learning").select(
            "id,action_key,q_value,visits,last_reward"
        ).eq("company_id", company_id).eq("state_key", state_key).execute()
        return result.data or []
    except Exception as exc:
        print("[QLEARN READ ERROR]", type(exc).__name__, exc)
        return []


def choose_action(company_id: int, context: dict[str, Any]) -> dict[str, Any]:
    state_key = _state_key(context)
    rows = _rows(company_id, state_key)
    values = {row.get("action_key"): float(row.get("q_value") or 0) for row in rows}
    for action in ACTIONS:
        values.setdefault(action, 0.0)

    # Deterministic exploration is disabled in production unless explicitly enabled.
    explore = os.getenv("BITEY_Q_EXPLORE", "false").lower() == "true"
    if explore and random.random() < EPSILON:
        action = random.choice(ACTIONS)
        mode = "explore"
    else:
        action = max(ACTIONS, key=lambda item: (values[item], item == "use_context" and context.get("has_history")))
        mode = "exploit"

    print(f"[QLEARN] linked=true state={state_key} action={action} q={values[action]:.4f} mode={mode}")
    return {
        "engine": "q_learning",
        "linked": True,
        "state_key": state_key,
        "action": action,
        "q_value": values[action],
        "mode": mode,
        "visits": next((int(r.get("visits") or 0) for r in rows if r.get("action_key") == action), 0),
    }


def _upsert(company_id: int, state_key: str, action: str, q_value: float, reward: float, transition: dict[str, Any]) -> bool:
    try:
        database.table("bitey_q_learning").upsert({
            "company_id": company_id,
            "state_key": state_key,
            "action_key": action,
            "q_value": float(q_value),
            "visits": 1,
            "last_reward": float(reward),
            "last_transition": transition,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="company_id,state_key,action_key").execute()
        return True
    except Exception as exc:
        print("[QLEARN WRITE ERROR]", type(exc).__name__, exc)
        return False


def learn(company_id: int, policy: dict[str, Any], reward: float, next_context: dict[str, Any]) -> dict[str, Any]:
    if not policy or not policy.get("linked"):
        return {"linked": False, "updated": False}

    state_key = str(policy["state_key"])
    action = str(policy["action"])
    rows = _rows(company_id, state_key)
    current = next((r for r in rows if r.get("action_key") == action), None)
    old_q = float(current.get("q_value") or 0) if current else 0.0
    visits = int(current.get("visits") or 0) if current else 0

    next_policy = choose_action(company_id, next_context)
    next_rows = _rows(company_id, str(next_policy["state_key"]))
    next_max = max([float(r.get("q_value") or 0) for r in next_rows] + [0.0])
    target = float(reward) + GAMMA * next_max
    new_q = old_q + ALPHA * (target - old_q)

    ok = _upsert(
        company_id, state_key, action, new_q, reward,
        {"reward": reward, "next_state": next_policy["state_key"], "next_action": next_policy["action"]}
    )
    if ok:
        try:
            database.table("bitey_q_learning").update({"visits": visits + 1}).eq("company_id", company_id).eq("state_key", state_key).eq("action_key", action).execute()
        except Exception as exc:
            print("[QLEARN VISIT ERROR]", type(exc).__name__, exc)

    print(f"[QLEARN] update=true action={action} reward={reward:.2f} old={old_q:.4f} new={new_q:.4f}")
    return {"linked": True, "updated": ok, "reward": reward, "old_q": old_q, "new_q": new_q}


def reward_for_turn(policy: dict[str, Any], *, response: str, history: list[dict[str, Any]], state: dict[str, Any]) -> float:
    """Conservative online reward: context use and clarification are rewarded only when supported."""
    action = policy.get("action")
    text = response.lower()
    reward = 0.0

    if action == "use_context" and history:
        reward += 0.8
        if any(token in text for token in ("antes", "mencionaste", "dijiste", "hablamos", "me dijiste")):
            reward += 0.7
    elif action == "ask_clarification":
        reward += 0.4 if "?" in response else -0.3
    elif action == "investigate":
        reward += 0.5 if "?" in response else 0.0
    elif action == "answer_direct":
        reward += 0.4 if response.strip() else -0.5

    if state.get("is_follow_up") and history:
        reward += 0.2
    if state.get("pending_question") and "?" in response:
        reward += 0.2

    return max(-1.0, min(2.0, reward))
