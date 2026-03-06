"""Tests for AI-powered anomaly analyzer."""

import json
import os
from unittest.mock import MagicMock, patch

from aegis.models import AttackType, ThreatLevel
from aegis.sentinels.ai_analyzer import (
    _build_analysis_prompt,
    _format_context,
    _format_events_for_context,
    _parse_ai_response,
    analyze_anomaly_with_ai,
    map_attack_type_to_enum,
    map_threat_level_str_to_enum,
    should_use_ai_analysis,
)


class TestFormatEventsForContext:
    """Tests for _format_events_for_context."""

    def test_empty_events(self):
        """Should return message when no events."""
        result = _format_events_for_context([])
        assert result == "No recent events available."

    def test_formats_events(self):
        """Should format events with name, block, and args."""
        mock_event = MagicMock()
        mock_event.event_name = "Transfer"
        mock_event.block_number = 12345
        mock_event.args = {"from": "0xabc", "to": "0xdef", "amount": 1000}

        result = _format_events_for_context([mock_event])

        assert "Transfer" in result
        assert "12345" in result
        assert "from=0xabc" in result

    def test_limits_to_20_events(self):
        """Should only include first 20 events."""
        events = []
        for i in range(25):
            mock_event = MagicMock()
            mock_event.event_name = f"Event{i}"
            mock_event.block_number = i
            mock_event.args = {}
            events.append(mock_event)

        result = _format_events_for_context(events)

        # Should have events 0-19, not 20-24
        assert "Event0" in result
        assert "Event19" in result
        assert "Event20" not in result


class TestFormatContext:
    """Tests for _format_context."""

    def test_formats_liquidity_context(self):
        """Should format liquidity-related fields."""
        context = {
            "protocol_address": "0x1234567890abcdef",
            "sentinel_type": "liquidity",
            "current_tvl": 1_000_000 * 10**18,  # 1M ETH
            "previous_tvl": 1_200_000 * 10**18,
            "change_percent": -16.67,
        }

        result = _format_context(context)

        assert "0x1234567890abcdef" in result
        assert "liquidity" in result
        assert "1,000,000" in result  # Formatted TVL
        assert "-16.67" in result

    def test_formats_oracle_context(self):
        """Should format oracle-related fields."""
        context = {
            "sentinel_type": "oracle",
            "chainlink_price": 3500.50,
            "protocol_price": 3400.00,
            "price_deviation": 2.87,
            "feed_age": 120,
        }

        result = _format_context(context)

        assert "oracle" in result
        assert "3500.50" in result
        assert "3400.00" in result
        assert "2.87" in result
        assert "120s" in result

    def test_formats_indicators(self):
        """Should format threshold indicators."""
        context = {
            "indicators": [
                "TVL dropped 25%",
                "Large withdrawal detected",
            ]
        }

        result = _format_context(context)

        assert "TVL dropped 25%" in result
        assert "Large withdrawal detected" in result

    def test_handles_empty_context(self):
        """Should handle empty context gracefully."""
        result = _format_context({})
        assert result == ""


class TestParseAiResponse:
    """Tests for _parse_ai_response."""

    def test_parses_valid_json(self):
        """Should parse valid JSON response."""
        response = json.dumps({
            "threat_level": "HIGH",
            "confidence": 0.85,
            "reasoning": "Detected flash loan pattern",
            "attack_type": "flash_loan",
        })

        result = _parse_ai_response(response)

        assert result["threat_level"] == "HIGH"
        assert result["confidence"] == 0.85
        assert result["reasoning"] == "Detected flash loan pattern"
        assert result["attack_type"] == "flash_loan"

    def test_parses_json_in_markdown_block(self):
        """Should extract JSON from markdown code block."""
        response = """Here's my analysis:

```json
{
    "threat_level": "CRITICAL",
    "confidence": 0.95,
    "reasoning": "Reentrancy attack detected",
    "attack_type": "reentrancy"
}
```

This appears to be a serious threat."""

        result = _parse_ai_response(response)

        assert result["threat_level"] == "CRITICAL"
        assert result["attack_type"] == "reentrancy"

    def test_parses_json_in_generic_code_block(self):
        """Should extract JSON from generic code block."""
        response = """Analysis:

```
{"threat_level": "MEDIUM", "confidence": 0.7, "reasoning": "test", "attack_type": "unknown"}
```
"""

        result = _parse_ai_response(response)

        assert result["threat_level"] == "MEDIUM"
        assert result["confidence"] == 0.7

    def test_normalizes_threat_level(self):
        """Should normalize invalid threat levels to HIGH."""
        response = json.dumps({
            "threat_level": "INVALID",
            "confidence": 0.5,
            "reasoning": "test",
            "attack_type": "unknown",
        })

        result = _parse_ai_response(response)

        assert result["threat_level"] == "HIGH"

    def test_normalizes_lowercase_threat_level(self):
        """Should uppercase threat level."""
        response = json.dumps({
            "threat_level": "critical",
            "confidence": 0.5,
            "reasoning": "test",
            "attack_type": "unknown",
        })

        result = _parse_ai_response(response)

        assert result["threat_level"] == "CRITICAL"

    def test_clamps_confidence(self):
        """Should clamp confidence to 0-1 range."""
        response = json.dumps({
            "threat_level": "HIGH",
            "confidence": 1.5,  # Invalid
            "reasoning": "test",
            "attack_type": "unknown",
        })

        result = _parse_ai_response(response)

        assert result["confidence"] == 1.0

    def test_normalizes_attack_type(self):
        """Should normalize invalid attack types to unknown."""
        response = json.dumps({
            "threat_level": "HIGH",
            "confidence": 0.5,
            "reasoning": "test",
            "attack_type": "INVALID_TYPE",
        })

        result = _parse_ai_response(response)

        assert result["attack_type"] == "unknown"

    def test_handles_malformed_json(self):
        """Should return conservative defaults for malformed JSON."""
        response = "This is not valid JSON at all"

        result = _parse_ai_response(response)

        assert result["threat_level"] == "HIGH"
        assert result["confidence"] == 0.6
        assert "parsing failed" in result["reasoning"].lower()

    def test_handles_missing_fields(self):
        """Should provide defaults for missing fields."""
        response = json.dumps({"threat_level": "LOW"})

        result = _parse_ai_response(response)

        assert result["threat_level"] == "LOW"
        assert "confidence" in result
        assert "reasoning" in result
        assert "attack_type" in result


class TestBuildAnalysisPrompt:
    """Tests for _build_analysis_prompt."""

    def test_builds_liquidity_prompt(self):
        """Should build prompt for liquidity analysis."""
        context = {
            "sentinel_type": "liquidity",
            "current_tvl": 500_000 * 10**18,
            "change_percent": -25.0,
        }

        prompt = _build_analysis_prompt("liquidity", context)

        assert "liquidity" in prompt.lower()
        assert "threat_level" in prompt
        assert "confidence" in prompt
        assert "JSON" in prompt

    def test_builds_oracle_prompt(self):
        """Should build prompt for oracle analysis."""
        context = {
            "sentinel_type": "oracle",
            "chainlink_price": 3500.0,
            "protocol_price": 3200.0,
            "price_deviation": 8.57,
        }

        prompt = _build_analysis_prompt("oracle", context)

        assert "oracle" in prompt.lower()
        assert "flash loan" in prompt.lower()
        assert "manipulation" in prompt.lower()

    def test_includes_attack_patterns(self):
        """Should mention attack patterns to look for."""
        prompt = _build_analysis_prompt("liquidity", {})

        assert "reentrancy" in prompt.lower()
        assert "flash loan" in prompt.lower()


class TestShouldUseAiAnalysis:
    """Tests for should_use_ai_analysis."""

    def test_returns_true_when_key_set(self):
        """Should return True when ANTHROPIC_API_KEY is set."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"}):
            assert should_use_ai_analysis() is True

    def test_returns_false_when_key_not_set(self):
        """Should return False when ANTHROPIC_API_KEY is not set."""
        env_copy = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env_copy:
            del env_copy["ANTHROPIC_API_KEY"]
        with patch.dict(os.environ, env_copy, clear=True):
            assert should_use_ai_analysis() is False


class TestMapAttackTypeToEnum:
    """Tests for map_attack_type_to_enum."""

    def test_maps_flash_loan(self):
        assert map_attack_type_to_enum("flash_loan") == AttackType.FLASH_LOAN

    def test_maps_reentrancy(self):
        assert map_attack_type_to_enum("reentrancy") == AttackType.REENTRANCY

    def test_maps_oracle_manipulation(self):
        assert map_attack_type_to_enum("oracle_manipulation") == AttackType.ORACLE_MANIPULATION

    def test_maps_rugpull_to_access_control(self):
        assert map_attack_type_to_enum("rugpull") == AttackType.ACCESS_CONTROL

    def test_maps_unknown_to_other(self):
        assert map_attack_type_to_enum("unknown") == AttackType.OTHER

    def test_maps_invalid_to_other(self):
        assert map_attack_type_to_enum("invalid_type") == AttackType.OTHER


class TestMapThreatLevelStrToEnum:
    """Tests for map_threat_level_str_to_enum."""

    def test_maps_valid_levels(self):
        assert map_threat_level_str_to_enum("NONE") == ThreatLevel.NONE
        assert map_threat_level_str_to_enum("LOW") == ThreatLevel.LOW
        assert map_threat_level_str_to_enum("MEDIUM") == ThreatLevel.MEDIUM
        assert map_threat_level_str_to_enum("HIGH") == ThreatLevel.HIGH
        assert map_threat_level_str_to_enum("CRITICAL") == ThreatLevel.CRITICAL

    def test_maps_invalid_to_high(self):
        """Should default to HIGH for invalid values."""
        assert map_threat_level_str_to_enum("INVALID") == ThreatLevel.HIGH


class TestAnalyzeAnomalyWithAi:
    """Tests for analyze_anomaly_with_ai."""

    def test_skips_analysis_without_api_key(self):
        """Should return defaults when API key not set."""
        env_copy = os.environ.copy()
        if "ANTHROPIC_API_KEY" in env_copy:
            del env_copy["ANTHROPIC_API_KEY"]

        with patch.dict(os.environ, env_copy, clear=True):
            context = {
                "threshold_threat_level": "CRITICAL",
                "current_tvl": 500_000 * 10**18,
            }

            result = analyze_anomaly_with_ai("liquidity", context)

            assert result["threat_level"] == "CRITICAL"  # Preserves threshold
            assert "API key not configured" in result["reasoning"]

    @patch("aegis.sentinels.ai_analyzer._get_agent_for_sentinel")
    def test_handles_agent_error(self, mock_get_agent):
        """Should return conservative defaults on agent error."""
        mock_get_agent.side_effect = RuntimeError("Agent creation failed")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            context = {"threshold_threat_level": "HIGH"}
            result = analyze_anomaly_with_ai("liquidity", context)

            assert result["threat_level"] == "HIGH"
            assert "failed" in result["reasoning"].lower()

    def test_successful_analysis(self):
        """Should process successful AI analysis."""
        # We need to mock at multiple levels since CrewAI has strict validation
        mock_response = json.dumps({
            "threat_level": "CRITICAL",
            "confidence": 0.95,
            "reasoning": "Flash loan attack pattern detected",
            "attack_type": "flash_loan",
        })

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch("aegis.sentinels.ai_analyzer.Agent") as mock_agent_class:
                with patch("aegis.sentinels.ai_analyzer.Task"):
                    # Set up mock agent
                    mock_agent = MagicMock()
                    mock_agent.execute_task.return_value = mock_response
                    mock_agent_class.return_value = mock_agent

                    # Clear cached agents to use mocked ones
                    import aegis.sentinels.ai_analyzer as ai_module
                    ai_module._liquidity_ai_agent = None
                    ai_module._oracle_ai_agent = None

                    context = {
                        "threshold_threat_level": "HIGH",
                        "current_tvl": 500_000 * 10**18,
                    }

                    result = analyze_anomaly_with_ai("liquidity", context)

                    assert result["threat_level"] == "CRITICAL"
                    assert result["confidence"] == 0.95
                    assert result["attack_type"] == "flash_loan"
                    mock_agent.execute_task.assert_called_once()

                    # Reset for other tests
                    ai_module._liquidity_ai_agent = None
                    ai_module._oracle_ai_agent = None


class TestLiquiditySentinelAiIntegration:
    """Integration tests for liquidity sentinel with AI."""

    def test_monitor_tvl_without_ai(self):
        """Should work without AI when use_ai=False."""
        from aegis.sentinels.liquidity_sentinel import monitor_tvl, set_previous_tvl

        # Set up previous TVL
        set_previous_tvl(1_000_000 * 10**18)

        # 25% drop - should trigger CRITICAL
        result = monitor_tvl(
            protocol_address="0x1234",
            current_tvl=750_000 * 10**18,
            use_ai=False,
        )

        assert result.threat_level == ThreatLevel.CRITICAL
        assert result.confidence == 0.95

    def test_monitor_tvl_skips_ai_for_low_threats(self):
        """Should not invoke AI for LOW/MEDIUM/NONE threats."""
        from aegis.sentinels.liquidity_sentinel import monitor_tvl, set_previous_tvl

        # Set up previous TVL
        set_previous_tvl(1_000_000 * 10**18)

        # 3% drop - should be NONE (below threshold)
        with patch("aegis.sentinels.ai_analyzer.analyze_anomaly_with_ai") as mock_ai:
            result = monitor_tvl(
                protocol_address="0x1234",
                current_tvl=970_000 * 10**18,
                use_ai=True,
            )

            assert result.threat_level == ThreatLevel.NONE
            mock_ai.assert_not_called()


class TestOracleSentinelAiIntegration:
    """Integration tests for oracle sentinel with AI."""

    def test_monitor_price_feeds_without_ai(self):
        """Should work without AI when use_ai=False."""
        from aegis.models import PriceFeedData
        from aegis.sentinels.oracle_sentinel import monitor_price_feeds
        from aegis.utils import now_seconds

        chainlink_data = PriceFeedData(
            price=3500.0,
            updated_at=now_seconds(),
            decimals=8,
            feed_address="0x1234",
        )

        # 6% deviation - should trigger CRITICAL
        result = monitor_price_feeds(
            protocol_price=3290.0,  # 6% below chainlink
            chainlink_data=chainlink_data,
            use_ai=False,
        )

        assert result.threat_level == ThreatLevel.CRITICAL
        assert result.confidence == 0.95

    def test_monitor_price_feeds_skips_ai_for_low_threats(self):
        """Should not invoke AI for LOW/MEDIUM/NONE threats."""
        from aegis.models import PriceFeedData
        from aegis.sentinels.oracle_sentinel import monitor_price_feeds
        from aegis.utils import now_seconds

        chainlink_data = PriceFeedData(
            price=3500.0,
            updated_at=now_seconds(),
            decimals=8,
            feed_address="0x1234",
        )

        # 1% deviation - should be NONE (below threshold)
        with patch("aegis.sentinels.ai_analyzer.analyze_anomaly_with_ai") as mock_ai:
            result = monitor_price_feeds(
                protocol_price=3465.0,  # ~1% below
                chainlink_data=chainlink_data,
                use_ai=True,
            )

            assert result.threat_level == ThreatLevel.NONE
            mock_ai.assert_not_called()
