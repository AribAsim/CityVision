from typing import Dict, List, Optional
from dataclasses import dataclass


SEVERITY_TIERS = ["Low", "Medium", "High", "Critical"]


@dataclass
class SeverityRulesConfig:
    # Baseline confidence thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.65

    # Base anomaly weights
    base_class_scores: Dict[str, int] = None

    # Observation count repeat boost thresholds
    repeat_observation_threshold: int = 3
    repeat_score_bonus: int = 10

    # Multi-bus confirmation bonus
    multi_bus_threshold: int = 2
    multi_bus_score_bonus: int = 15

    def __post_init__(self):
        if self.base_class_scores is None:
            self.base_class_scores = {
                "Pothole": 70,
                "Crack-Severe": 55,
                "Crack": 30,
                "Speed-Bump": 20,
                "Rash-Driving": 90,
            }


# Default global rules configuration (can be modified at runtime)
DEFAULT_RULES = SeverityRulesConfig()


def calculate_base_severity(confidence: float, config: SeverityRulesConfig = DEFAULT_RULES) -> str:
    """
    Initial transparent rule-based severity based on detection confidence:
    HIGH: confidence >= 0.85
    MEDIUM: confidence >= 0.65
    LOW: confidence < 0.65
    """
    if confidence >= config.high_confidence_threshold:
        return "High"
    elif confidence >= config.medium_confidence_threshold:
        return "Medium"
    return "Low"


def escalate_tier(current_severity: str, steps: int = 1) -> str:
    """Escalate severity tier by N steps, capped strictly at 'Critical'."""
    try:
        idx = SEVERITY_TIERS.index(current_severity)
    except ValueError:
        idx = 1  # default to Medium if unknown
    new_idx = min(idx + steps, len(SEVERITY_TIERS) - 1)
    return SEVERITY_TIERS[new_idx]


def compute_priority_score(
    anomaly_type: str,
    confidence: float,
    confirmation_count: int,
    unique_bus_count: int,
    config: SeverityRulesConfig = DEFAULT_RULES
) -> int:
    """
    Deterministic priority score calculation (0 - 100):
    1. Base score from anomaly type & confidence.
    2. Repeated observation bonus if confirmation_count >= 3.
    3. Multi-bus confirmation bonus if unique_bus_count >= 2.
    """
    base_weight = config.base_class_scores.get(anomaly_type, 30)
    score = base_weight * confidence

    # Repeated observation bonus
    if confirmation_count >= config.repeat_observation_threshold:
        score += config.repeat_score_bonus

    # Multi-bus verification bonus
    if unique_bus_count >= config.multi_bus_threshold:
        score += config.multi_bus_score_bonus

    return int(max(0, min(100, round(score))))


def evaluate_incident_severity(
    initial_severity: str,
    confirmation_count: int,
    unique_bus_count: int,
    config: SeverityRulesConfig = DEFAULT_RULES
) -> str:
    """
    Evaluate and escalate incident severity based on cumulative evidence:
    - If multiple distinct buses report it (unique_bus_count >= 2), escalate 1 tier.
    - If repeatedly observed (confirmation_count >= 3) and still Low/Medium, escalate 1 tier.
    """
    severity = initial_severity

    escalation_steps = 0
    if unique_bus_count >= config.multi_bus_threshold:
        escalation_steps += 1

    if confirmation_count >= config.repeat_observation_threshold and escalation_steps == 0:
        escalation_steps += 1

    return escalate_tier(severity, steps=escalation_steps)
