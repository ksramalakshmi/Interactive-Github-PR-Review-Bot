from app.agents.bug import BugAgent
from app.agents.security import SecurityAgent
from app.agents.performance import PerformanceAgent
from app.agents.style import StyleAgent

AGENTS = [
    BugAgent(),
    SecurityAgent(),
    PerformanceAgent(),
    StyleAgent(),
]