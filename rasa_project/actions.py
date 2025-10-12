from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType

# --- GENERATED STUBS ---

MOODS = [{"enables": {"actions": ["action_greet", "action_offer_help"], "intents": ["greet", "ask_help", "smalltalk", "affirm", "deny"]}, "enter_animation": "wave_small", "idle_loop": "breathe_calm", "name": "friendly", "transitions": [{"side_effects": [{"emit_animation": "brow_furrow"}], "to": "concerned", "when": "user_sentiment \u003c -0.3"}], "weights": {"actions": {"action_greet": 1.4, "action_offer_help": 1.2}}}, {"enables": {"actions": ["action_collect_details", "action_escalate"], "intents": ["report_problem", "cancel", "escalate"]}, "enter_animation": "lean_in", "idle_loop": "breathe_fast", "masks": {"intents": ["smalltalk"]}, "name": "concerned", "transitions": [{"to": "friendly", "when": "issue_resolved == true"}]}]

def current_mood(tracker: Tracker) -> Text:
    return tracker.get_slot("mood") or "friendly"

class ActionMoodTick(Action):
    def name(self) -> Text:
        return "action_mood_tick"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:
        """Evaluate transitions and set `mood` slot accordingly.
        In production you would call your Mood Controller; here we compute a toy transition:
        - If slot issue_resolved == true → friendly
        - Else if slot user_sentiment < -0.3 → concerned
        """
        sentiment = tracker.get_slot("user_sentiment") or 0.0
        issue_resolved = tracker.get_slot("issue_resolved") or False

        cur = current_mood(tracker)
        nxt = cur

        try:
            s = float(sentiment)
        except Exception:
            s = 0.0

        if bool(issue_resolved):
            nxt = "friendly"
        elif s < -0.3:
            nxt = "concerned"

        events: List[EventType] = []
        if nxt != cur:
            events.append(SlotSet("mood", nxt))
        return events

class ActionUtterMooded(Action):
    def name(self) -> Text:
        return "action_utter_mooded"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:
        """Route a response by mood; for the demo we hardcode greet variants."""
        m = current_mood(tracker)
        key = f"utter_greet__{m}"
        responses = domain.get("responses", {})
        if key in responses:
            template = responses[key][0].get("text", f"[{key}]")
            dispatcher.utter_message(text=template)
        else:
            dispatcher.utter_message(text="Hello.")
        return []