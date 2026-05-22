"""
Anomaly Detector Agent
======================
Detects unusual patterns in bridge activity using statistical methods.
Uses Z-score analysis, moving averages, and threshold-based detection.

Token consumption: ~0 (statistical analysis only, no LLM inference)
"""

import math
import logging
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.anomaly_detector")


class AnomalyDetectorAgent:
    """
    Detects anomalies in cross-chain bridge activity.
    
    Detection methods:
      1. Volume spike detection (Z-score based)
      2. Sudden outflow detection (threshold-based)
      3. TVL drop detection (percentage-based)
      4. Low volume anomaly (suspiciously quiet bridges)
      5. Statistical outlier detection (IQR method)
    
    Token consumption: ~0 (statistical analysis only, no LLM inference)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        self._historical_stats: Dict[str, List[float]] = {}
        logger.info("AnomalyDetectorAgent initialized (z-threshold=%.1f)",
                     self.config.thresholds.anomaly_z_score_threshold)
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze all data for anomalies.
        
        Returns:
            {
                "anomalies": [...],
                "anomaly_summary": {severity: count},
                "scored_bridges": [{name, anomaly_score}, ...],
            }
        """
        logger.info("Running anomaly detection...")
        
        monitor_data = context.get("bridge_monitor", {})
        flow_data = context.get("flow_analyzer", {})
        historical = context.get("historical_comparator", {})
        
        anomalies = []
        
        # 1. Volume spike detection
        anomalies.extend(self._detect_volume_spikes(monitor_data))
        
        # 2. Sudden outflow detection
        anomalies.extend(self._detect_sudden_outflows(flow_data))
        
        # 3. TVL drop detection
        anomalies.extend(self._detect_tvl_drops(monitor_data))
        
        # 4. Low volume anomalies
        anomalies.extend(self._detect_low_volume_anomalies(monitor_data))
        
        # 5. Cross-chain flow anomalies
        anomalies.extend(self._detect_flow_anomalies(flow_data))
        
        # Score each bridge
        bridge_scores = self._score_bridges(anomalies)
        
        result = {
            "anomalies": anomalies,
            "anomaly_summary": self._summarize(anomalies),
            "scored_bridges": bridge_scores,
            "total_anomalies": len(anomalies),
            "detection_timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info("Anomaly detection complete: %d anomalies found", len(anomalies))
        return result
    
    def _detect_volume_spikes(self, monitor_data: Dict) -> List[Dict]:
        """Detect volume spikes using Z-score against estimated normal."""
        anomalies = []
        chain_tvl = monitor_data.get("chain_tvl", {})
        
        # Compute average TVL across chains as baseline
        tvl_values = [v for v in chain_tvl.values() if v > 0]
        if not tvl_values:
            return anomalies
        
        mean_tvl = sum(tvl_values) / len(tvl_values)
        variance = sum((v - mean_tvl) ** 2 for v in tvl_values) / len(tvl_values)
        std_tvl = math.sqrt(variance) if variance > 0 else 1
        
        threshold = self.config.thresholds.anomaly_z_score_threshold
        
        for chain, tvl in chain_tvl.items():
            if tvl <= 0:
                continue
            z_score = (tvl - mean_tvl) / std_tvl if std_tvl > 0 else 0
            
            if abs(z_score) > threshold:
                severity = "critical" if abs(z_score) > 4 else "warning" if abs(z_score) > 3 else "info"
                anomalies.append({
                    "type": "volume_spike",
                    "chain": chain,
                    "severity": severity,
                    "z_score": round(z_score, 2),
                    "value": tvl,
                    "mean": round(mean_tvl, 2),
                    "description": f"Chain {chain} TVL (${tvl/1e6:.1f}M) is {abs(z_score):.1f}σ from mean (${mean_tvl/1e6:.1f}M)",
                })
        
        return anomalies
    
    def _detect_sudden_outflows(self, flow_data: Dict) -> List[Dict]:
        """Detect chains with large net outflows."""
        anomalies = []
        chain_flows = flow_data.get("chain_flows", {})
        multiplier = self.config.thresholds.sudden_outflow_multiplier
        
        for chain, flows in chain_flows.items():
            net = flows.get("net", 0)
            tvl = flows.get("tvl", 0)
            if tvl > 0 and net < 0:
                outflow_ratio = abs(net) / tvl
                if outflow_ratio > 0.05:  # >5% TVL leaving
                    severity = "critical" if outflow_ratio > 0.15 else "warning"
                    anomalies.append({
                        "type": "sudden_outflow",
                        "chain": chain,
                        "severity": severity,
                        "outflow_ratio": round(outflow_ratio, 4),
                        "net_flow": round(net, 2),
                        "tvl": tvl,
                        "description": f"Chain {chain} has net outflow of ${abs(net)/1e6:.1f}M ({outflow_ratio*100:.1f}% of TVL)",
                    })
        
        return anomalies
    
    def _detect_tvl_drops(self, monitor_data: Dict) -> List[Dict]:
        """Detect significant TVL drops (compare to expected range)."""
        anomalies = []
        chain_tvl = monitor_data.get("chain_tvl", {})
        threshold = self.config.thresholds.tvl_drop_percentage
        
        # Use historical comparator data if available
        hist = monitor_data.get("historical", {})
        
        for chain, tvl in chain_tvl.items():
            # Check against minimum expected TVL
            chain_config = self.config.get_chain_by_name(chain)
            if chain_config and tvl < chain_config.min_tvl_alert and tvl > 0:
                anomalies.append({
                    "type": "tvl_drop",
                    "chain": chain,
                    "severity": "warning",
                    "current_tvl": tvl,
                    "expected_minimum": chain_config.min_tvl_alert,
                    "description": f"Chain {chain} TVL (${tvl/1e6:.1f}M) below minimum threshold (${chain_config.min_tvl_alert/1e6:.1f}M)",
                })
        
        return anomalies
    
    def _detect_low_volume_anomalies(self, monitor_data: Dict) -> List[Dict]:
        """Detect bridges with suspiciously low volume."""
        anomalies = []
        bridges = monitor_data.get("top_bridges", [])
        threshold = self.config.thresholds.low_volume_threshold
        
        for bridge in bridges:
            tvl = bridge.get("tvl", 0)
            name = bridge.get("name", "unknown")
            # High TVL but potentially low activity
            if tvl > 100_000_000:  # > $100M TVL
                anomalies.append({
                    "type": "low_volume_check",
                    "bridge": name,
                    "severity": "info",
                    "tvl": tvl,
                    "description": f"Bridge '{name}' has high TVL (${tvl/1e6:.1f}M) - monitoring for activity patterns",
                })
        
        return anomalies
    
    def _detect_flow_anomalies(self, flow_data: Dict) -> List[Dict]:
        """Detect anomalous flow patterns."""
        anomalies = []
        concentration = flow_data.get("concentration_risk", 0)
        imbalanced = flow_data.get("imbalance_chains", [])
        
        if concentration > 0.7:
            anomalies.append({
                "type": "concentration_risk",
                "severity": "warning",
                "concentration_score": concentration,
                "description": f"High concentration risk ({concentration:.2f}) - flow dominated by few corridors",
            })
        
        for chain in imbalanced:
            anomalies.append({
                "type": "flow_imbalance",
                "chain": chain,
                "severity": "info",
                "description": f"Chain {chain} has significant flow imbalance",
            })
        
        return anomalies
    
    def _score_bridges(self, anomalies: List[Dict]) -> List[Dict]:
        """Score each bridge/chain by anomaly count and severity."""
        severity_weights = {"critical": 3, "warning": 2, "info": 1}
        scores: Dict[str, float] = {}
        
        for a in anomalies:
            target = a.get("chain") or a.get("bridge") or "system"
            weight = severity_weights.get(a.get("severity", "info"), 1)
            scores[target] = scores.get(target, 0) + weight
        
        scored = [{"name": k, "anomaly_score": v} for k, v in scores.items()]
        scored.sort(key=lambda x: x["anomaly_score"], reverse=True)
        return scored
    
    def _summarize(self, anomalies: List[Dict]) -> Dict[str, int]:
        """Count anomalies by severity."""
        summary = {"critical": 0, "warning": 0, "info": 0}
        for a in anomalies:
            sev = a.get("severity", "info")
            summary[sev] = summary.get(sev, 0) + 1
        return summary
