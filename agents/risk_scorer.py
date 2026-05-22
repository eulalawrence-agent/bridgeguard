"""
Risk Scorer Agent
=================
Computes comprehensive risk scores for bridges and chains.
Combines TVL, volume, anomaly, exploit, and historical data.

Token consumption: ~0 (scoring algorithm only)
"""

import math
import logging
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.risk_scorer")


class RiskScorerAgent:
    """
    Computes risk scores for bridges and chains.
    
    Scoring factors:
      - TVL size and stability
      - Volume consistency
      - Anomaly count and severity
      - Exploit indicator count
      - Flow concentration risk
      - Historical performance
    
    Token consumption: ~0 (scoring algorithm only)
    """
    
    # Weight factors for composite score
    WEIGHTS = {
        "tvl_stability": 0.15,
        "volume_consistency": 0.10,
        "anomaly_score": 0.25,
        "exploit_score": 0.25,
        "concentration_risk": 0.10,
        "historical_score": 0.15,
    }
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        logger.info("RiskScorerAgent initialized with %d weight factors", len(self.WEIGHTS))
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute risk scores for all monitored entities.
        
        Returns:
            {
                "chain_scores": {chain: {score, factors, grade}},
                "bridge_scores": [...],
                "overall_risk": float,
                "risk_grade": str,
            }
        """
        logger.info("Computing risk scores...")
        
        monitor_data = context.get("bridge_monitor", {})
        flow_data = context.get("flow_analyzer", {})
        anomaly_data = context.get("anomaly_detector", {})
        exploit_data = context.get("exploit_detector", {})
        historical = context.get("historical_comparator", {})
        
        chain_scores = {}
        for chain in self.config.monitored_chains:
            score_data = self._score_chain(
                chain.name, monitor_data, flow_data, anomaly_data, exploit_data, historical
            )
            chain_scores[chain.name] = score_data
        
        # Score individual bridges
        bridge_scores = self._score_bridges(monitor_data, exploit_data)
        
        # Overall risk
        if chain_scores:
            overall = sum(s["score"] for s in chain_scores.values()) / len(chain_scores)
        else:
            overall = 0
        
        result = {
            "chain_scores": chain_scores,
            "bridge_scores": bridge_scores[:20],
            "overall_risk": round(overall, 1),
            "risk_grade": self._grade_risk(overall),
            "scoring_timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info("Risk scoring complete: overall=%.1f, grade=%s", overall, result["risk_grade"])
        return result
    
    def _score_chain(self, chain_name: str, monitor: Dict, flow: Dict,
                     anomaly: Dict, exploit: Dict, historical: Dict) -> Dict:
        """Compute risk score for a single chain."""
        factors = {}
        
        # TVL stability factor (0-100, higher = more stable = lower risk)
        tvl = monitor.get("chain_tvl", {}).get(chain_name, 0)
        chain_config = self.config.get_chain_by_name(chain_name)
        if chain_config and chain_config.min_tvl_alert > 0:
            tvl_ratio = min(tvl / chain_config.min_tvl_alert, 2.0)
            factors["tvl_stability"] = min(tvl_ratio * 50, 100)
        else:
            factors["tvl_stability"] = 50
        
        # Volume consistency
        vol = flow.get("chain_flows", {}).get(chain_name, {}).get("volume", 0)
        factors["volume_consistency"] = min(100, vol / 1_000_000 * 10) if vol > 0 else 20
        
        # Anomaly score (inverted: more anomalies = lower score = higher risk)
        anomaly_score = 0
        for a in anomaly.get("anomalies", []):
            if a.get("chain") == chain_name:
                sev_weight = {"critical": 30, "warning": 15, "info": 5}
                anomaly_score += sev_weight.get(a.get("severity", "info"), 5)
        factors["anomaly_score"] = max(0, 100 - anomaly_score)
        
        # Exploit score
        exploit_score = 0
        for e in exploit.get("exploits", []):
            if e.get("chain") == chain_name:
                exploit_score += e.get("confidence", 0.5) * 40
        factors["exploit_score"] = max(0, 100 - exploit_score)
        
        # Concentration risk
        factors["concentration_risk"] = max(0, 100 - flow.get("concentration_risk", 0) * 100)
        
        # Historical score
        factors["historical_score"] = historical.get("chain_scores", {}).get(chain_name, 70)
        
        # Composite score (weighted average)
        composite = sum(
            factors.get(k, 50) * v for k, v in self.WEIGHTS.items()
        )
        
        return {
            "score": round(composite, 1),
            "factors": {k: round(v, 1) for k, v in factors.items()},
            "grade": self._grade_risk(composite),
            "tvl": tvl,
        }
    
    def _score_bridges(self, monitor: Dict, exploit: Dict) -> List[Dict]:
        """Score individual bridges."""
        bridges = monitor.get("top_bridges", [])
        scores = []
        
        high_risk_names = {b["name"] for b in exploit.get("high_risk_bridges", [])}
        
        for bridge in bridges:
            name = bridge.get("name", "unknown")
            tvl = bridge.get("tvl", 0)
            
            # Base score from TVL (larger = generally more reliable)
            base = min(100, tvl / 50_000_000 * 50) if tvl > 0 else 10
            
            # Penalty if flagged
            if name in high_risk_names:
                base *= 0.5
            
            scores.append({
                "name": name,
                "score": round(base, 1),
                "tvl": tvl,
                "flagged": name in high_risk_names,
                "grade": self._grade_risk(base),
            })
        
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores
    
    def _grade_risk(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 80:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 35:
            return "D"
        else:
            return "F"
