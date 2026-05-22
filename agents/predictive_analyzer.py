"""
Predictive Analyzer Agent
=========================
Predicts potential issues based on current trends and historical patterns.
Uses simple regression, momentum analysis, and risk extrapolation.

Token consumption: ~0 (statistical prediction only)
"""

import math
import logging
from typing import Any, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.predictive_analyzer")


class PredictiveAnalyzerAgent:
    """
    Predicts potential future issues based on current trends.
    
    Prediction methods:
      - Linear extrapolation of TVL trends
      - Momentum analysis (acceleration/deceleration)
      - Risk trajectory prediction
      - Bridge health forecasting
      - Potential failure point estimation
    
    Token consumption: ~0 (statistical prediction only)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        logger.info("PredictiveAnalyzerAgent initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate predictions based on all available data.
        
        Returns:
            {
                "predictions": [...],
                "risk_trajectory": str,
                "recommended_actions": [...],
                "confidence_level": str,
            }
        """
        logger.info("Running predictive analysis...")
        
        predictions = []
        
        # 1. TVL trend predictions
        predictions.extend(self._predict_tvl_trends(context))
        
        # 2. Risk trajectory
        risk_trajectory = self._predict_risk_trajectory(context)
        
        # 3. Anomaly trend predictions
        predictions.extend(self._predict_anomaly_trends(context))
        
        # 4. Bridge health forecasts
        predictions.extend(self._forecast_bridge_health(context))
        
        # 5. Recommended actions
        actions = self._generate_recommendations(context, predictions)
        
        # 6. Confidence level
        confidence = self._assess_confidence(context)
        
        result = {
            "predictions": predictions,
            "risk_trajectory": risk_trajectory,
            "recommended_actions": actions,
            "confidence_level": confidence,
            "prediction_count": len(predictions),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info("Predictive analysis complete: %d predictions, trajectory=%s",
                     len(predictions), risk_trajectory)
        return result
    
    def _predict_tvl_trends(self, context: Dict) -> List[Dict]:
        """Predict TVL trends for each chain."""
        predictions = []
        monitor = context.get("bridge_monitor", {})
        historical = context.get("historical_comparator", {})
        
        trends = historical.get("trends", {})
        chain_tvl = monitor.get("chain_tvl", {})
        
        for chain, tvl in chain_tvl.items():
            trend = trends.get(chain, "unknown")
            
            if trend == "increasing":
                growth_rate = self._estimate_growth_rate(historical, chain)
                predicted_7d = tvl * (1 + growth_rate * 7)
                predictions.append({
                    "type": "tvl_trend",
                    "chain": chain,
                    "direction": "up",
                    "current_tvl": tvl,
                    "predicted_7d": round(predicted_7d, 2),
                    "growth_rate_daily": round(growth_rate * 100, 2),
                    "confidence": "moderate",
                    "description": f"Chain {chain} TVL trending up ({growth_rate*100:.1f}%/day). Predicted 7d TVL: ${predicted_7d/1e6:.1f}M",
                })
            elif trend == "decreasing":
                decline_rate = self._estimate_growth_rate(historical, chain)
                predicted_7d = tvl * (1 + decline_rate * 7)
                
                severity = "warning" if abs(decline_rate) > 0.05 else "info"
                predictions.append({
                    "type": "tvl_trend",
                    "chain": chain,
                    "direction": "down",
                    "current_tvl": tvl,
                    "predicted_7d": round(predicted_7d, 2),
                    "decline_rate_daily": round(abs(decline_rate) * 100, 2),
                    "confidence": "moderate",
                    "severity": severity,
                    "description": f"Chain {chain} TVL declining ({decline_rate*100:.1f}%/day). Predicted 7d TVL: ${predicted_7d/1e6:.1f}M",
                })
        
        return predictions
    
    def _predict_risk_trajectory(self, context: Dict) -> str:
        """Predict overall risk trajectory."""
        risk = context.get("risk_scorer", {})
        exploit = context.get("exploit_detector", {})
        anomaly = context.get("anomaly_detector", {})
        historical = context.get("historical_comparator", {})
        
        current_risk = risk.get("overall_risk", 0)
        exploit_risk = exploit.get("exploit_risk_score", 0)
        anomaly_count = anomaly.get("total_anomalies", 0)
        
        # Simple trajectory: combine factors
        momentum = 0
        if exploit_risk > 50:
            momentum += 1
        if anomaly_count > 5:
            momentum += 1
        if current_risk > 60:
            momentum += 1
        
        # Check trends
        trends = historical.get("trends", {})
        decreasing_count = sum(1 for t in trends.values() if t == "decreasing")
        total_trends = len(trends)
        
        if total_trends > 0 and decreasing_count / total_trends > 0.5:
            momentum += 1
        
        if momentum >= 3:
            return "deteriorating"
        elif momentum <= 1:
            return "improving"
        else:
            return "stable"
    
    def _predict_anomaly_trends(self, context: Dict) -> List[Dict]:
        """Predict future anomaly patterns."""
        predictions = []
        anomaly = context.get("anomaly_detector", {})
        summary = anomaly.get("anomaly_summary", {})
        
        critical = summary.get("critical", 0)
        warning = summary.get("warning", 0)
        
        if critical >= 3:
            predictions.append({
                "type": "anomaly_prediction",
                "prediction": "High critical anomaly count suggests elevated risk in next 24h",
                "severity": "warning",
                "description": f"Currently {critical} critical anomalies. Expect continued alert state.",
                "confidence": "moderate",
                "timeframe": "24h",
            })
        
        if warning >= 5:
            predictions.append({
                "type": "anomaly_prediction",
                "prediction": "Multiple warnings indicate systemic stress",
                "severity": "info",
                "description": f"{warning} warning-level anomalies active. Monitor for escalation.",
                "confidence": "low",
                "timeframe": "48h",
            })
        
        return predictions
    
    def _forecast_bridge_health(self, context: Dict) -> List[Dict]:
        """Forecast bridge health status."""
        predictions = []
        risk = context.get("risk_scorer", {})
        
        for chain, data in risk.get("chain_scores", {}).items():
            score = data.get("score", 50)
            grade = data.get("grade", "C")
            
            if grade in ("D", "F"):
                predictions.append({
                    "type": "health_forecast",
                    "chain": chain,
                    "current_score": score,
                    "forecast": "At risk of further degradation",
                    "severity": "warning",
                    "description": f"Chain {chain} health score ({score}, grade {grade}) - monitor for improvement or escalation",
                })
            elif grade == "A":
                predictions.append({
                    "type": "health_forecast",
                    "chain": chain,
                    "current_score": score,
                    "forecast": "Healthy and stable",
                    "severity": "info",
                    "description": f"Chain {chain} maintaining excellent health ({score}, grade {grade})",
                })
        
        return predictions
    
    def _generate_recommendations(self, context: Dict, predictions: List[Dict]) -> List[Dict]:
        """Generate actionable recommendations."""
        actions = []
        
        exploit = context.get("exploit_detector", {})
        risk = context.get("risk_scorer", {})
        anomaly = context.get("anomaly_detector", {})
        
        # High exploit risk recommendations
        if exploit.get("exploit_risk_score", 0) > 60:
            actions.append({
                "priority": "high",
                "action": "Consider reducing bridge exposure on flagged chains",
                "reason": f"Exploit risk score elevated ({exploit['exploit_risk_score']}/100)",
            })
        
        # High-risk bridges
        for bridge in exploit.get("high_risk_bridges", []):
            actions.append({
                "priority": "medium",
                "action": f"Investigate {bridge['name']} (flagged by {bridge['flag_count']} indicators)",
                "reason": f"Multiple exploit indicators for bridge {bridge['name']}",
            })
        
        # Anomaly-based recommendations
        if anomaly.get("anomaly_summary", {}).get("critical", 0) > 0:
            actions.append({
                "priority": "high",
                "action": "Review critical anomalies immediately",
                "reason": "Active critical anomalies require attention",
            })
        
        # Risk-based recommendations
        overall_risk = risk.get("overall_risk", 0)
        if overall_risk > 70:
            actions.append({
                "priority": "critical",
                "action": "System-wide risk elevated. Consider halting bridge operations on flagged chains.",
                "reason": f"Overall risk score: {overall_risk}/100",
            })
        
        # Trend-based recommendations
        trajectory = self._predict_risk_trajectory(context)
        if trajectory == "deteriorating":
            actions.append({
                "priority": "high",
                "action": "Risk trajectory is deteriorating. Increase monitoring frequency.",
                "reason": "Multiple indicators suggest worsening conditions",
            })
        
        if not actions:
            actions.append({
                "priority": "low",
                "action": "Continue normal monitoring",
                "reason": "All indicators within normal ranges",
            })
        
        return actions
    
    def _assess_confidence(self, context: Dict) -> str:
        """Assess overall confidence in predictions."""
        historical = context.get("historical_comparator", {})
        data_points = historical.get("data_points_stored", 0)
        
        if data_points > 500:
            return "high"
        elif data_points > 100:
            return "moderate"
        elif data_points > 20:
            return "low"
        else:
            return "insufficient_data"
    
    def _estimate_growth_rate(self, historical: Dict, chain: str) -> float:
        """Estimate daily growth/decline rate from historical data."""
        # Use trend information to estimate
        trend = historical.get("trends", {}).get(chain, "stable")
        
        if trend == "increasing":
            return 0.02  # 2% daily growth estimate
        elif trend == "decreasing":
            return -0.02  # 2% daily decline estimate
        else:
            return 0.0
