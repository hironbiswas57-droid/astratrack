"""
AstraTrack AI - Nova: Novice Celestial Navigator & Space Mentor Agent
Provides pedagogical, beginner-friendly astronomical guidance, guided interactive tours,
and plain-English analogies for clients who are new to stargazing and celestial mechanics.
"""

from typing import Dict, List, Any, Optional
from ..database import (
    get_or_create_client,
    update_client_profile,
    get_client_preferences,
    record_client_history
)

# Curated interactive beginner tours
NOVICE_TOURS = {
    "tour_nav_101": {
        "id": "tour_nav_101",
        "title": "Stargazing 101: Finding Polaris & The Big Dipper",
        "icon": "🧭",
        "description": "Learn how ancient navigators used the Big Dipper pointer stars to locate True North, and how Earth's axis changes over thousands of years.",
        "steps": [
            {
                "step": 1,
                "title": "Welcome to the Celestial Dome (2026 CE)",
                "explanation": "You're viewing the northern night sky in the year 2026. Notice the bright stars and constellation lines. You can click and drag anywhere on the canvas to look in any direction, and use your mouse wheel to zoom in!",
                "ui_action": {"action": "switch_view", "value": "planetarium"},
                "epoch": 2026,
                "tip": "Try dragging the sky right now to orient yourself!"
            },
            {
                "step": 2,
                "title": "The Big Dipper (Ursa Major) Pointer Stars",
                "explanation": "Find Ursa Major (the Great Bear). The two stars on the outer edge of the dipper's bowl (Merak and Dubhe) form a straight line pointing directly toward Polaris, our current North Star.",
                "ui_action": {"action": "set_epoch", "value": 2026},
                "epoch": 2026,
                "tip": "Polaris doesn't move as the Earth spins each night; everything else wheels around it!"
            },
            {
                "step": 3,
                "title": "Time-Travel to Ancient Egypt (-2800 BCE)",
                "explanation": "Let's leap back 4,800 years! Notice that Polaris is NO LONGER near the North Celestial Pole! Back when the Great Pyramids were built, Earth's axis pointed to Thuban (in Draco). The pyramids' interior shafts were carved to align with Thuban.",
                "ui_action": {"action": "set_epoch", "value": -2800},
                "epoch": -2800,
                "tip": "Look at the red crosshairs at the center: Thuban is right there!"
            },
            {
                "step": 4,
                "title": "The Vega Golden Age (+13,700 CE)",
                "explanation": "Now we warp into the far future (+13,700 CE). Earth's wobble completes half its grand cycle, and the brilliant blue star Vega becomes our glorious North Pole star!",
                "ui_action": {"action": "set_epoch", "value": 13700},
                "epoch": 13700,
                "tip": "Vega is 50 times brighter than Polaris, lighting up future polar nights."
            }
        ]
    },
    "tour_defense_101": {
        "id": "tour_defense_101",
        "title": "Planetary Defense: Tracking Near-Earth Asteroids",
        "icon": "🛰️",
        "description": "Discover how space sentinels like JWST, NEOWISE, and ground radars track asteroids on potential collision courses with Earth.",
        "steps": [
            {
                "step": 1,
                "title": "Switching to Orbital Sentinel View",
                "explanation": "Welcome to Orbital Sentinel Mode! Here we look down on our inner Solar System. The yellow disc at the center is the Sun, and the cyan orbit is Earth.",
                "ui_action": {"action": "switch_view", "value": "orbital"},
                "tip": "Drag to orbit the 3D plane and scroll to zoom in close to Earth."
            },
            {
                "step": 2,
                "title": "Tracking Asteroid 99942 Apophis",
                "explanation": "Apophis is a 370-meter wide space rock. On Friday, April 13, 2029, it will safely pass just 31,600 km from Earth's surface — closer than our television satellites! It will be visible to the naked eye for billions of people.",
                "ui_action": {"action": "focus_orbital_body", "value": "apophis"},
                "tip": "Click on any asteroid card in the left Astral Radar panel to lock your radar telescope onto it."
            },
            {
                "step": 3,
                "title": "Space Sentinels on Watch",
                "explanation": "NASA's NEOWISE infrared space telescope and the James Webb Space Telescope (JWST) detect dark asteroids using heat emissions (thermal infrared) rather than reflected sunlight, giving us decades of advance warning.",
                "ui_action": {"action": "focus_orbital_body", "value": "apophis"},
                "tip": "Early detection allows deflection missions like NASA's DART to nudge asteroids off course."
            }
        ]
    },
    "tour_seasons_101": {
        "id": "tour_seasons_101",
        "title": "Ancient Stargazers: Reading Seasons in the Stars",
        "icon": "🌾",
        "description": "Before clocks and calendars existed, civilizations used the dawn rising of bright stars to know when to plant crops and prepare for seasonal floods.",
        "steps": [
            {
                "step": 1,
                "title": "The Egyptian Star Clock (Sirius)",
                "explanation": "Sirius is the brightest star in our night sky. In ancient Egypt, when Sirius appeared in the dawn twilight right before sunrise in mid-summer, it was a reliable harbinger that the Nile river was about to flood, revitalizing their farmland.",
                "ui_action": {"action": "highlight_season", "value": "Summer"},
                "tip": "Check the left sidebar 'Helio-Phenology' tab to view active stellar rules for this epoch!"
            },
            {
                "step": 2,
                "title": "The Pleiades Planting Guide",
                "explanation": "The Greek poet Hesiod wrote in 700 BCE: 'When the Pleiades daughters of Atlas arise, begin your harvest; and begin plowing when they go down.' Star clusters served as Earth's ancient agricultural clock.",
                "ui_action": {"action": "switch_view", "value": "planetarium"},
                "tip": "Look for the tiny cluster of blue stars known as the Seven Sisters (M45)."
            }
        ]
    }
}


class NovaAgent:
    """
    Pedagogical AI Agent dedicated to novice clients, offering plain-English explanations,
    interactive guided tours, and empathy for newcomers to astronomy.
    """

    def __init__(self):
        self.agent_name = "Nova"
        self.avatar = "🌟"
        self.role = "Novice Celestial Navigator & Space Mentor"

    def is_novice_query(self, query: str, client_level: str = "novice") -> bool:
        """Determines if query asks for beginner help or if client is in novice mode."""
        q = query.lower()
        novice_signals = [
            "help", "guide", "novice", "beginner", "newbie", "new to", "start",
            "how to use", "what is this", "tour", "explain simply", "simple words",
            "what does that mean", "where do i start", "how do i look", "easy",
            "basics", "teach me", "tutorial", "walkthrough", "learn"
        ]
        if any(signal in q for signal in novice_signals):
            return True
        # If client profile is marked as novice and asking general questions
        return client_level == "novice"

    def analyze(self, query: str, current_year: float, client_id: str = "default_client") -> Dict[str, Any]:
        """
        Produce beginner-friendly guidance, friendly analogies, and interactive tour options.
        """
        # Fetch or update client profile memory
        client = get_or_create_client(client_id)
        q_lower = query.lower()

        # Check if user wants to change their experience level
        if "i am an expert" in q_lower or "expert mode" in q_lower:
            update_client_profile(client_id, experience_level="expert", novice_mode_active=False)
            thought = "Recognized client mastery request. Switching interface profile to Expert Astrometric Sentinel."
            insights = [
                "**Skill Level Updated**: Profile calibrated to **Expert Astrometric Sentinel**.",
                "Raw numerical ephemerides and orbital state vectors are now prioritized in your telemetry.",
                "You can switch back to Novice Guide anytime by typing `'help me'` or `'I am a beginner'`."
            ]
            return {
                "agent": self.agent_name,
                "role": self.role,
                "avatar": self.avatar,
                "thought": thought,
                "insights": insights,
                "ui_actions": [{"action": "set_client_level", "value": "expert"}]
            }

        if "i am a beginner" in q_lower or "novice mode" in q_lower:
            update_client_profile(client_id, experience_level="novice", novice_mode_active=True)

        # Detect if a specific tour is requested
        selected_tour = None
        if "asteroid" in q_lower or "defense" in q_lower or "apophis" in q_lower or "orbital" in q_lower:
            selected_tour = NOVICE_TOURS["tour_defense_101"]
        elif "season" in q_lower or "egypt" in q_lower or "sirius" in q_lower or "harvest" in q_lower:
            selected_tour = NOVICE_TOURS["tour_seasons_101"]
        else:
            selected_tour = NOVICE_TOURS["tour_nav_101"]

        # Record tour recommendation in client memory
        record_client_history(client_id, "recommend_tour", {"tour_id": selected_tour["id"]})

        thought = (
            f"Detected client query for introductory celestial exploration. "
            f"Tailoring guidance with intuitive analogies (spinning-top precession, pointer stars) "
            f"and launching interactive tour directive: '{selected_tour['title']}'."
        )

        insights = [
            f"**Welcome, Explorer!**: Astronomy doesn't have to be overwhelming. Think of the night sky like a giant clock that takes 25,772 years to make a single tick!",
            f"**What is Precession?**: Imagine spinning a toy top on a table. As it spins, its tip slowly draws a wide wobbling circle in the air. Earth's axis does the exact same thing over 26,000 years, pointing at different 'North Stars' across human history!",
            f"**Recommended Guided Tour**: **{selected_tour['icon']} {selected_tour['title']}** — *{selected_tour['description']}*",
            f"**How to Navigate**: Use the bottom **Epoch Slider** to scrub backwards and forwards in time, or click any of the quick-epoch pills like **2,800 BCE (Pyramids)** to see how the sky looked to ancient pharaohs!"
        ]

        return {
            "agent": self.agent_name,
            "role": self.role,
            "avatar": self.avatar,
            "thought": thought,
            "insights": insights,
            "recommended_tour": selected_tour,
            "available_tours": list(NOVICE_TOURS.values()),
            "ui_actions": [
                {"action": "suggest_tour", "value": selected_tour["id"]},
                {"action": "set_client_level", "value": "novice"}
            ]
        }


# Singleton Nova agent instance
nova_agent = NovaAgent()
