"""
Alert Generator Agent
=====================
Generates actionable alerts from anomaly, exploit, and risk data.
Formats alerts for console output with severity levels.

Token consumption: ~0 (formatting and threshold checks only)
"""

import logging
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.alert_generator")


class AlertGeneratorAgent:
    """
    Generates alerts based on analysis pipeline results.
    
    Alert types:
      - CRITICAL: Potential exploit, extreme TVL movement
      - WARNING: Anomaly detected, elevated risk
      - INFO: Notable activity, informational
    
    Token consumption: ~0 (formatting and threshold checks only)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        self.alert_history: List[Dict] = []
        logger.info("AlertGeneratorAgent initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate alerts from all analysis results.
        
        Returns:
            {
                "alerts": [...],
                "alert_counts": {severity: count},
                "top_alerts": [...],
                "alert_summary": str,
            }
        """
        logger.info("Generating alerts...")
        
        alerts = []
        
        # Alerts from anomalies
        alerts.extend(self._anomaly_alerts(context.get("anomaly_detector", {})))
        
        # Alerts from exploit detector
        alerts.extend(self._exploit_alerts(context.get("exploit_detector", {})))
        
        # Alerts from risk scorer
        alerts.extend(self._risk_alerts(context.get("risk_scorer", {})))
        
        # Alerts from flow analyzer
        alerts.extend(self._flow_alerts(context.get("flow_analyzer", {})))
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a.get("severity", "info"), 3))
        
        # Deduplicate
        alerts = self._deduplicate(alerts)
        
        counts = {
            "critical": len([a for a in alerts if a["severity"] == "critical"]),
            "warning": len([a for a in alerts if a["severity"] == "warning"]),
            "info": len([a for a in alerts if a["severity"] == "info"]),
        }
        
        result = {
            "alerts": alerts,
            "alert_counts": counts,
            "top_alerts": alerts[:10],
            "total_alerts": len(alerts),
            "alert_summary": self._generate_summary(alerts, counts),
            "generation_timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info("Generated %d alerts (C:%d W:%d I:%d)",
                     len(alerts), counts["critical"], counts["warning"], counts["info"])
        return result
    
    def _anomaly_alerts(self, anomaly_data: Dict) -> List[Dict]:
        """Generate alerts from anomaly detector results."""
        alerts = []
        for anomaly in anomaly_data.get("anomalies", []):
            if anomaly.get("severity") in ("critical", "warning"):
                alerts.append({
                    "id": f"ANOM-{hash(str(anomaly)) % 10000:04d}",
                    "type": "anomaly",
                    "severity": anomaly["severity"],
                    "title": f"Anomaly: {anomaly['type'].replace('_', ' ').title()}",
                    "description": anomaly.get("description", "Anomaly detected"),
                    "chain": anomaly.get("chain", "N/A"),
                    "data": anomaly,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts
    
    def _exploit_alerts(self, exploit_data: Dict) -> List[Dict]:
        """Generate alerts from exploit detector results."""
        alerts = []
        for exploit in exploit_data.get("exploits", []):
            if exploit.get("confidence", 0) >= 0.3:
                alerts.append({
                    "id": f"EXP-{hash(str(exploit)) % 10000:04d}",
                    "type": "exploit",
                    "severity": exploit.get("severity", "warning"),
                    "title": f"Exploit Risk: {exploit['type'].replace('_', ' ').title()}",
                    "description": exploit.get("description", "Potential exploit detected"),
                    "chain": exploit.get("chain", "N/A"),
                    "confidence": exploit.get("confidence", 0),
                    "mitigation": exploit.get("mitigation", "Monitor closely"),
                    "data": exploit,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts
    
    def _risk_alerts(self, risk_data: Dict) -> List[Dict]:
        """Generate alerts from risk scorer results."""
        alerts = []
        overall_risk = risk_data.get("overall_risk", 0)
        
        if overall_risk >= self.config.thresholds.risk_score_critical:
            alerts.append({
                "id": f"RISK-{int(datetime.utcnow().timestamp()) % 10000:04d}",
                "type": "risk",
                "severity": "critical",
                "title": f"Critical Overall Risk Score: {overall_risk}",
                "description": f"System-wide risk score ({overall_risk}) exceeds critical threshold",
                "chain": "SYSTEM",
                "data": {"overall_risk": overall_risk},
                "timestamp": datetime.utcnow().isoformat(),
            })
        elif overall_risk >= self.config.thresholds.risk_score_warning:
            alerts.append({
                "id": f"RISK-{int(datetime.utcnow().timestamp()) % 10000:04d}",
                "type": "risk",
                "severity": "warning",
                "title": f"Elevated Risk Score: {overall_risk}",
                "description": f"System-wide risk score ({overall_risk}) is elevated",
                "chain": "SYSTEM",
                "data": {"overall_risk": overall_risk},
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Individual chain risk alerts
        for chain, score_data in risk_data.get("chain_scores", {}).items():
            if score_data.get("score", 100) < 40:
                alerts.append({
                    "id": f"CHAIN-RISK-{hash(chain) % 10000:04d}",
                    "type": "risk",
                    "severity": "warning",
                    "title": f"High Risk Chain: {chain}",
                    "description": f"Chain {chain} risk score: {score_data['score']} ({score_data['grade']})",
                    "chain": chain,
                    "data": score_data,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        
        return alerts
    
    def _flow_alerts(self, flow_data: Dict) -> List[Dict]:
        """Generate alerts from flow analysis."""
        alerts = []
        
        if flow_data.get("concentration_risk", 0) > 0.7:
            alerts.append({
                "id": f"FLOW-{int(datetime.utcnow().timestamp()) % 10000:04d}",
                "type": "flow",
                "severity": "warning",
                "title": "High Flow Concentration Risk",
                "description": f"Cross-chain flows are highly concentrated (risk: {flow_data['concentration_risk']:.2f})",
                "chain": "MULTI",
                "data": {"concentration_risk": flow_data["concentration_risk"]},
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        for chain in flow_data.get("imbalance_chains", []):
            alerts.append({
                "id": f"IMBAL-{hash(chain) % 10000:04d}",
                "type": "flow",
                "severity": "info",
                "title": f"Flow Imbalance: {chain}",
                "description": f"Significant flow imbalance detected on {chain}",
                "chain": chain,
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return alerts
    
    def _deduplicate(self, alerts: List[Dict]) -> List[Dict]:
        """Remove duplicate alerts."""
        seen = set()
        unique = []
        for alert in alerts:
            key = (alert.get("type"), alert.get("chain"), alert.get("title"))
            if key not in seen:
                seen.add(key)
                unique.append(alert)
        return unique
    
    def _generate_summary(self, alerts: List[Dict], counts: Dict) -> str:
        """Generate human-readable alert summary."""
        total = len(alerts)
        if total == 0:
            return "✅ No alerts - all systems nominal."
        
        parts = [f"📊 {total} alert(s) generated:"]
        if counts["critical"]:
            parts.append(f"  🔴 {counts['critical']} CRITICAL")
        if counts["warning"]:
            parts.append(f"  🟡 {counts['warning']} WARNING")
        if counts["info"]:
            parts.append(f"  🔵 {counts['info']} INFO")
        
        return "\n".join(parts)
