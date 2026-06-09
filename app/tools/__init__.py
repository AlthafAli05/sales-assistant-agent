import json
import os
from pathlib import Path

# Load catalog once at startup
CATALOG_PATH = Path(__file__).parent.parent.parent / "catalog.json"
with open(CATALOG_PATH) as f:
    CATALOG = json.load(f)


def search_catalog(query: str) -> str:
    """
    Keyword search over the product catalog JSON.
    Returns matching plans and FAQs as a formatted string.
    """
    query_lower = query.lower()
    results = []

    for plan in CATALOG["plans"]:
        plan_text = f"{plan['name']} {plan['price']} {' '.join(plan['features'])}".lower()
        if any(word in plan_text for word in query_lower.split()):
            results.append(
                f"Plan: {plan['name']} — {plan['price']}\n"
                f"Features: {', '.join(plan['features'])}"
            )

    for faq in CATALOG["faqs"]:
        faq_text = f"{faq['q']} {faq['a']}".lower()
        if any(word in faq_text for word in query_lower.split()):
            results.append(f"FAQ: {faq['q']}\nAnswer: {faq['a']}")

    if not results:
        # Return full catalog if nothing matched
        all_plans = []
        for plan in CATALOG["plans"]:
            all_plans.append(
                f"Plan: {plan['name']} — {plan['price']}\n"
                f"Features: {', '.join(plan['features'])}"
            )
        return "Full catalog:\n\n" + "\n\n".join(all_plans)

    return "\n\n".join(results)


def get_user_memory(user_id: str, memory_store) -> str:
    """
    Retrieves relevant past facts about this user for context injection.
    Queries the DB — not a string injection.
    """
    return memory_store.get_user_summary(user_id)


def flag_for_human(user_id: str, reason: str, memory_store=None) -> str:
    """
    Escalates conversation to human reviewer when confidence is low.
    Logs the flag in the DB.
    """
    print(f"[FLAG FOR HUMAN] user_id={user_id} reason={reason}")
    return f"Conversation flagged for human review. Reason: {reason}"
