"""
Historical Comparator Agent
===========================
Compares current bridge data with historical patterns.
Uses rolling averages, standard deviations, and trend detection.

Token consumption: ~0 (statistical comparison only)
"""

import math
import json
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("bridgeguard.agents.historical_comparator")


class HistoricalComparatorAgent:
    """
    Compares current data with historical baselines.
    
    Methods:
      - Rolling average comparison
      - Standard deviation analysis
      - Trend detection (up/down/stable)
      - Seasonal pattern matching
      - Historical anomaly correlation
    
    Token consumption: ~0 (statistical comparison only)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        self.history_file = os.path.join(self.config.data_dir, "history.json")
        self._load_history()
        logger.info("HistoricalComparatorAgent initialized (%d historical data points)",
                     sum(len(v) for v in self._history.values()))
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current state with historical patterns.
        
        Returns:
            {
                "chain_scores": {chain: score},
                "trends": {chain: trend},
                "deviations": [{chain, metric, deviation}, ...],
                "historical_baseline": {...},
            }
        """
        logger.info("Running historical comparison...")
        
        monitor = context.get("bridge_monitor", {})
        chain_tvl = monitor.get("chain_tvl", {})
        
        # Store current data point
        self._store_snapshot(chain_tvl)
        
        # Compare with history
        chain_scores = {}
        trends = {}
        deviations = []
        
        for chain, tvl in chain_tvl.items():
            history = self._history.get(chain, [])
            
            if len(history) >= 3:
                # Compute rolling statistics
                recent = history[-30:]  # Last 30 data points
                mean = sum(h["tvl"] for h in recent) / len(recent)
                variance = sum((h["tvl"] - mean) ** 2 for h in recent) / len(recent)
                std = math.sqrt(variance) if variance > 0 else mean * 0.1
                
                # Z-score of current vs historical
                z_score = (tvl - mean) / std if std > 0 else 0
                
                # Score: 100 = perfectly normal, lower = more deviation
                score = max(0, min(100, 100 - abs(z_score) * 20))
                
                # Trend detection
                if len(recent) >= 5:
                    short_recent = [h["tvl"] for h in recent[-5:]]
                    trend = self._detect_trend(short_recent)
                else:
                    trend = "insufficient_data"
                
                chain_scores[chain] = round(score, 1)
                trends[chain] = trend
                
                if abs(z_score) > 1.5:
                    deviations.append({
                        "chain": chain,
                        "current_tvl": tvl,
                        "historical_mean": round(mean, 2),
                        "z_score": round(z_score, 2),
                        "deviation": "above" if z_score > 0 else "below",
                        "significance": "high" if abs(z_score) > 2.5 else "moderate",
                    })
            else:
                chain_scores[chain] = 70  # Default score for new chains
                trends[chain] = "new_chain"
        
        # Compute baseline
        baseline = self._compute_baseline()
        
        result = {
            "chain_scores": chain_scores,
            "trends": trends,
            "deviations": deviations,
            "historical_baseline": baseline,
            "data_points_stored": sum(len(v) for v in self._history.values()),
            "comparison_timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info("Historical comparison complete: %d deviations, %d data points",
                     len(deviations), result["data_points_stored"])
        return result
    
    def _detect_trend(self, values: List[float]) -> str:
        """Detect trend direction from recent values."""
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        relative_slope = slope / y_mean if y_mean > 0 else 0
        
        if relative_slope > 0.05:
            return "increasing"
        elif relative_slope < -0.05:
            return "decreasing"
        else:
            return "stable"
    
    def _store_snapshot(self, chain_tvl: Dict[str, float]) -> None:
        """Store current TVL snapshot for historical tracking."""
        timestamp = datetime.utcnow().isoformat()
        
        for chain, tvl in chain_tvl.items():
            if chain not in self._history:
                self._history[chain] = []
            self._history[chain].append({
                "tvl": tvl,
                "timestamp": timestamp,
            })
            # Keep last 100 data points per chain
            self._history[chain] = self._history[chain][-100:]
        
        self._save_history()
    
    def _compute_baseline(self) -> Dict[str, Any]:
        """Compute overall baseline statistics."""
        all_tvls = []
        for chain_history in self._history.values():
            for h in chain_history[-10:]:
                all_tvls.append(h["tvl"])
        
        if not all_tvls:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}
        
        mean = sum(all_tvls) / len(all_tvls)
        variance = sum((v - mean) ** 2 for v in all_tvls) / len(all_tvls)
        
        return {
            "mean": round(mean, 2),
            "std": round(math.sqrt(variance), 2),
            "min": round(min(all_tvls), 2),
            "max": round(max(all_tvls), 2),
            "sample_count": len(all_tvls),
        }
    
    def _load_history(self) -> None:
        """Load historical data from disk."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    self._history = json.load(f)
            else:
                self._history = {}
        except (json.JSONDecodeError, IOError):
            self._history = {}
    
    def _save_history(self) -> None:
        """Save historical data to disk."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(self._history, f)
        except IOError as e:
            logger.warning("Failed to save history: %s", e)
