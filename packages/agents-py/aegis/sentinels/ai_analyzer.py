"""AI-powered anomaly analyzer using CrewAI.

This module provides AI-enhanced threat analysis by using Claude to analyze
the context around anomalies detected by threshold-based sentinels. When
thresholds trigger HIGH or CRITICAL, the AI can:
1. CONFIRM the threat with additional context
2. DOWNGRADE the threat if it sees legitimate activity
3. Add contextual reasoning to the assessment
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any

from crewai import Agent, LLM, Task

from aegis.models import AttackType, ThreatLevel


def _get_anthropic_llm() -> LLM:
    """Get Anthropic Claude LLM for CrewAI agents."""
    return LLM(
        model="anthropic/claude-3-5-sonnet-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

if TYPE_CHECKING:
    from aegis.adapters.base import ProtocolEvent

logger = logging.getLogger(__name__)


# Attack patterns that AI should look for
ATTACK_PATTERNS = {
    "flash_loan": [
        "large borrow followed by repay in same block",
        "loan amount significantly exceeds normal volume",
        "borrow from multiple pools simultaneously",
    ],
    "reentrancy": [
        "repeated calls to same function in single tx",
        "withdrawal pattern: check-then-withdraw",
        "external calls before state updates",
    ],
    "oracle_manipulation": [
        "large swap before liquidation",
        "price deviation after concentrated trade",
        "sandwich pattern around price-sensitive operation",
    ],
    "rugpull": [
        "owner/admin withdrawal of significant funds",
        "sudden liquidity removal by deployer",
        "pause followed by privileged extraction",
    ],
    "legitimate": [
        "gradual rebalancing by known addresses",
        "scheduled protocol operations",
        "governance-approved migrations",
    ],
}


def _format_events_for_context(events: list[ProtocolEvent]) -> str:
    """Format protocol events into a readable string for AI analysis."""
    if not events:
        return "No recent events available."

    lines = []
    for event in events[:20]:  # Limit to most recent 20
        args_str = ", ".join(f"{k}={v}" for k, v in list(event.args.items())[:5])
        lines.append(
            f"  - {event.event_name} (block {event.block_number}): {args_str}"
        )
    return "\n".join(lines)


def _format_context(context: dict[str, Any]) -> str:
    """Format the full context dict into a readable analysis prompt."""
    parts = []

    if "protocol_address" in context:
        parts.append(f"Protocol Address: {context['protocol_address']}")

    if "sentinel_type" in context:
        parts.append(f"Sentinel Type: {context['sentinel_type']}")

    if "current_tvl" in context:
        tvl_eth = context["current_tvl"] / 10**18
        parts.append(f"Current TVL: {tvl_eth:,.4f} ETH")

    if "previous_tvl" in context:
        prev_eth = context["previous_tvl"] / 10**18
        parts.append(f"Previous TVL: {prev_eth:,.4f} ETH")

    if "change_percent" in context:
        parts.append(f"TVL Change: {context['change_percent']:.2f}%")

    if "chainlink_price" in context:
        parts.append(f"Chainlink Price: ${context['chainlink_price']:.2f}")

    if "protocol_price" in context:
        parts.append(f"Protocol Price: ${context['protocol_price']:.2f}")

    if "price_deviation" in context:
        parts.append(f"Price Deviation: {context['price_deviation']:.2f}%")

    if "feed_age" in context:
        parts.append(f"Price Feed Age: {context['feed_age']}s")

    if "threshold_threat_level" in context:
        parts.append(f"Threshold-Based Assessment: {context['threshold_threat_level']}")

    if "indicators" in context and context["indicators"]:
        parts.append("Threshold Indicators:")
        for ind in context["indicators"]:
            parts.append(f"  - {ind}")

    if "recent_events" in context:
        events = context["recent_events"]
        if events:
            parts.append(f"Recent Protocol Events ({len(events)} events):")
            parts.append(_format_events_for_context(events))
        else:
            parts.append("Recent Protocol Events: None available")

    return "\n".join(parts)


def _build_analysis_prompt(sentinel_type: str, context: dict[str, Any]) -> str:
    """Build the analysis prompt for the AI agent."""
    formatted_context = _format_context(context)

    prompt = f"""Analyze this {sentinel_type} anomaly detected by the AEGIS security system.

{formatted_context}

Your task is to determine if this anomaly represents a genuine security threat or
legitimate protocol activity. Consider:

1. **Is this normal market behavior or a potential exploit?**
   - Normal: gradual changes, known addresses, expected patterns
   - Suspicious: sudden changes, unknown addresses, attack patterns

2. **Are there signs of specific attack types?**
   - Flash loan: Large borrow + repay in same block
   - Reentrancy: Repeated function calls before state updates
   - Oracle manipulation: Large trades before price-sensitive operations
   - Rug pull: Admin/owner draining funds

3. **What is the evidence quality?**
   - Strong evidence: Multiple corroborating indicators
   - Weak evidence: Single indicator that could be coincidental

Based on your analysis, provide a JSON response with EXACTLY this structure:
{{
    "threat_level": "NONE|LOW|MEDIUM|HIGH|CRITICAL",
    "confidence": 0.0 to 1.0,
    "reasoning": "2-3 sentence explanation of your conclusion",
    "attack_type": "flash_loan|reentrancy|oracle_manipulation|rugpull|legitimate|unknown"
}}

IMPORTANT:
- If the threshold detection seems like a false positive, you MAY downgrade the threat level
- If you see additional attack indicators, you MAY upgrade the threat level
- Be conservative: when in doubt, maintain the threshold-based assessment
- Your confidence should reflect certainty in your assessment
"""
    return prompt


def _parse_ai_response(response: str) -> dict[str, Any]:
    """Parse the AI response, handling various formats.

    Returns a dict with threat_level, confidence, reasoning, attack_type.
    Falls back to defaults if parsing fails.
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON block
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            json_str = response[start:end].strip()
        elif "{" in response and "}" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            json_str = response[start:end]
        else:
            raise ValueError("No JSON found in response")

        result = json.loads(json_str)

        # Validate and normalize fields
        threat_level = result.get("threat_level", "HIGH").upper()
        if threat_level not in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            threat_level = "HIGH"

        confidence = float(result.get("confidence", 0.7))
        confidence = max(0.0, min(1.0, confidence))

        attack_type = result.get("attack_type", "unknown").lower()
        valid_attack_types = [
            "flash_loan",
            "reentrancy",
            "oracle_manipulation",
            "rugpull",
            "legitimate",
            "unknown",
        ]
        if attack_type not in valid_attack_types:
            attack_type = "unknown"

        return {
            "threat_level": threat_level,
            "confidence": confidence,
            "reasoning": result.get("reasoning", "AI analysis completed"),
            "attack_type": attack_type,
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning("Failed to parse AI response: %s", e)
        # Return conservative defaults
        return {
            "threat_level": "HIGH",
            "confidence": 0.6,
            "reasoning": "AI response parsing failed - maintaining threshold assessment",
            "attack_type": "unknown",
        }


# Lazy-loaded agent instances (to avoid requiring API key at import time)
_liquidity_ai_agent: Agent | None = None
_oracle_ai_agent: Agent | None = None


def _get_liquidity_ai_agent() -> Agent:
    """Get or create the Liquidity AI analyzer agent."""
    global _liquidity_ai_agent
    if _liquidity_ai_agent is None:
        _liquidity_ai_agent = Agent(
            role="Liquidity Security Analyst",
            goal=(
                "Analyze DeFi liquidity anomalies to determine if they represent "
                "genuine security threats or legitimate market activity. Provide "
                "evidence-based assessments that minimize both false positives and "
                "missed exploits."
            ),
            backstory=(
                "You are an expert DeFi security analyst with deep knowledge of "
                "flash loan attacks, rug pulls, and liquidity manipulation schemes. "
                "You've analyzed hundreds of exploits including Euler Finance, "
                "Cream Finance, and Beanstalk. You understand that sudden TVL drops "
                "can be exploits OR legitimate withdrawals, and you carefully examine "
                "the evidence before making a determination."
            ),
            llm=_get_anthropic_llm(),
            verbose=False,
            allow_delegation=False,
        )
    return _liquidity_ai_agent


def _get_oracle_ai_agent() -> Agent:
    """Get or create the Oracle AI analyzer agent."""
    global _oracle_ai_agent
    if _oracle_ai_agent is None:
        _oracle_ai_agent = Agent(
            role="Oracle Security Analyst",
            goal=(
                "Analyze price feed anomalies to determine if they represent "
                "oracle manipulation attacks or legitimate market movements. "
                "Distinguish between natural price volatility and malicious price "
                "manipulation attempts."
            ),
            backstory=(
                "You are an expert in DeFi oracle security and price manipulation "
                "attacks. You've studied exploits like Mango Markets, Harvest Finance, "
                "and various flash loan + oracle manipulation combinations. You "
                "understand how attackers manipulate AMM spot prices to trigger "
                "liquidations or extract value from lending protocols."
            ),
            llm=_get_anthropic_llm(),
            verbose=False,
            allow_delegation=False,
        )
    return _oracle_ai_agent


def _get_agent_for_sentinel(sentinel_type: str) -> Agent:
    """Get the appropriate AI agent for a sentinel type."""
    if sentinel_type == "liquidity":
        return _get_liquidity_ai_agent()
    elif sentinel_type == "oracle":
        return _get_oracle_ai_agent()
    else:
        # Default to liquidity agent for unknown types
        return _get_liquidity_ai_agent()


def analyze_anomaly_with_ai(
    sentinel_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Use AI to analyze an anomaly and determine if it's malicious.

    This function takes the context of an anomaly detected by threshold-based
    monitoring and uses CrewAI (with Claude) to perform deeper analysis.

    Args:
        sentinel_type: Type of sentinel ("liquidity", "oracle")
        context: Dict containing current state, recent events, etc.

    Returns:
        Dict with keys:
            - threat_level: "NONE"|"LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
            - confidence: float 0.0-1.0
            - reasoning: str explanation
            - attack_type: str classification

    Note:
        Requires ANTHROPIC_API_KEY environment variable to be set.
        If AI analysis fails, returns conservative defaults.
    """
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not set - skipping AI analysis")
        return {
            "threat_level": context.get("threshold_threat_level", "HIGH"),
            "confidence": 0.5,
            "reasoning": "AI analysis skipped - API key not configured",
            "attack_type": "unknown",
        }

    logger.info("=== AI ANALYSIS START ===")
    logger.info("Sentinel Type: %s", sentinel_type)
    logger.info("Context Keys: %s", list(context.keys()))

    try:
        # Get the appropriate agent
        agent = _get_agent_for_sentinel(sentinel_type)

        # Build the analysis prompt
        prompt = _build_analysis_prompt(sentinel_type, context)
        logger.debug("Analysis prompt:\n%s", prompt[:500] + "..." if len(prompt) > 500 else prompt)

        # Create and execute the task
        task = Task(
            description=prompt,
            expected_output="JSON object with threat_level, confidence, reasoning, attack_type",
            agent=agent,
        )

        # Execute the analysis
        result = agent.execute_task(task)
        logger.debug("Raw AI response: %s", result[:500] if len(str(result)) > 500 else result)

        # Parse the response
        parsed = _parse_ai_response(str(result))

        logger.info("AI Assessment:")
        logger.info("  Threat Level: %s", parsed["threat_level"])
        logger.info("  Confidence: %.2f", parsed["confidence"])
        logger.info("  Attack Type: %s", parsed["attack_type"])
        logger.info("  Reasoning: %s", parsed["reasoning"][:200])
        logger.info("=== AI ANALYSIS END ===")

        return parsed

    except Exception as e:
        logger.error("AI analysis failed: %s", e)
        logger.info("=== AI ANALYSIS END (FAILED) ===")

        # Return conservative defaults
        return {
            "threat_level": context.get("threshold_threat_level", "HIGH"),
            "confidence": 0.5,
            "reasoning": f"AI analysis failed: {e}",
            "attack_type": "unknown",
        }


def should_use_ai_analysis() -> bool:
    """Check if AI analysis should be used.

    Returns True if ANTHROPIC_API_KEY is set, False otherwise.
    """
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def map_attack_type_to_enum(attack_type_str: str) -> AttackType:
    """Map AI-returned attack type string to AttackType enum."""
    mapping = {
        "flash_loan": AttackType.FLASH_LOAN,
        "reentrancy": AttackType.REENTRANCY,
        "oracle_manipulation": AttackType.ORACLE_MANIPULATION,
        "rugpull": AttackType.ACCESS_CONTROL,
        "legitimate": AttackType.OTHER,
        "unknown": AttackType.OTHER,
    }
    return mapping.get(attack_type_str, AttackType.OTHER)


def map_threat_level_str_to_enum(threat_level_str: str) -> ThreatLevel:
    """Map AI-returned threat level string to ThreatLevel enum."""
    try:
        return ThreatLevel(threat_level_str)
    except ValueError:
        return ThreatLevel.HIGH
