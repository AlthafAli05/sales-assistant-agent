import os
import json
import uuid
from groq import Groq
from app.tools import search_catalog, get_user_memory, flag_for_human
from app.memory import MemoryStore

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Search the product catalog for pricing, features, and plan information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query about products or pricing"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_memory",
            "description": "Retrieve past conversation context and facts about this user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The user ID to retrieve memory for"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_for_human",
            "description": "Escalate conversation to a human reviewer when confidence is very low.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["user_id", "reason"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a helpful B2B SaaS sales assistant. You help potential customers understand 
our product plans, pricing, and features. Always use the search_catalog tool to answer 
product questions — never guess pricing or features from memory.

Always use get_user_memory at the start to recall what this user has asked before, 
so you can provide continuity across sessions.

Be concise, professional, and helpful."""


def run_agent(user_id: str, session_id: str, message: str, memory_store: MemoryStore) -> dict:
    tools_called = []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]

    # Agentic loop
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1000
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                tools_called.append(tool_name)

                if tool_name == "search_catalog":
                    result = search_catalog(tool_input["query"])
                elif tool_name == "get_user_memory":
                    result = get_user_memory(tool_input["user_id"], memory_store)
                elif tool_name == "flag_for_human":
                    result = flag_for_human(tool_input["user_id"], tool_input["reason"], memory_store)
                else:
                    result = "Tool not found."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            final_text = msg.content or ""
            break

    # Self-evaluation
    eval_block = _self_evaluate(message, final_text, tools_called)

    if eval_block["confidence"] < 0.6 and "flag_for_human" not in tools_called:
        flag_for_human(user_id, f"Low confidence: {eval_block['confidence']}", memory_store)
        eval_block["flagged"] = True

    return {
        "response": final_text,
        "eval": eval_block,
        "tools_called": tools_called,
        "session_id": session_id
    }


def _self_evaluate(user_message: str, agent_response: str, tools_called: list) -> dict:
    eval_prompt = f"""Evaluate this sales assistant response. Return ONLY valid JSON, no markdown, no extra text.

User asked: {user_message}
Assistant responded: {agent_response}
Tools used: {tools_called}

Return exactly this JSON:
{{"groundedness": 0.9, "relevance": 0.9, "confidence": 0.9, "flagged": false, "reasoning": "one sentence"}}"""

    eval_response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": eval_prompt}],
        max_tokens=200
    )

    try:
        eval_text = eval_response.choices[0].message.content.strip()
        if "```" in eval_text:
            eval_text = eval_text.split("```")[1]
            if eval_text.startswith("json"):
                eval_text = eval_text[4:]
        return json.loads(eval_text)
    except Exception:
        return {
            "groundedness": 0.75,
            "relevance": 0.75,
            "confidence": 0.75,
            "flagged": False,
            "reasoning": "Default scores applied."
        }
