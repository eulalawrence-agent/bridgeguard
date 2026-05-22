"""
BridgeGuard Orchestrator
========================
Main pipeline that coordinates all analysis agents.
Token consumption: ~0 (coordination logic only)
"""

import time
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.config import BridgeGuardConfig

logger = logging.getLogger("bridgeguard.orchestrator")


class Orchestrator:
    """
    Main pipeline orchestrator that coordinates all BridgeGuard agents.
    
    Pipeline flow:
        1. BridgeMonitorAgent  -> fetch live data
        2. FlowAnalyzerAgent   -> analyze fund flows
        3. HistoricalComparator -> compare with history
        4. AnomalyDetectorAgent -> detect anomalies
        5. ExploitDetectorAgent -> detect exploits
        6. RiskScorerAgent      -> score risk
        7. PredictiveAnalyzer   -> predict issues
        8. AlertGeneratorAgent  -> generate alerts
        9. ReportWriterAgent    -> write reports
    
    Token consumption: ~0 (coordination only, no LLM calls)
    """
    
    def __init__(self, config: Optional[BridgeGuardConfig] = None):
        self.config = config or BridgeGuardConfig()
        self.context: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "config": self.config,
            "pipeline_status": {},
        }
        self.agents: List[Any] = []
        self._results_cache: Dict[str, Any] = {}
        logger.info("Orchestrator initialized with %d monitored chains",
                     len(self.config.monitored_chains))
    
    def run_pipeline(self, mode: str = "full") -> Dict[str, Any]:
        """
        Run the full analysis pipeline.
        
        Args:
            mode: "full", "monitor", "analyze", "report", "alerts"
        
        Returns:
            Complete pipeline results dictionary.
        """
        start_time = time.time()
        self.context["mode"] = mode
        logger.info("Starting pipeline in '%s' mode", mode)
        
        # Import agents lazily to avoid circular imports
        from agents.bridge_monitor import BridgeMonitorAgent
        from agents.flow_analyzer import FlowAnalyzerAgent
        from agents.anomaly_detector import AnomalyDetectorAgent
        from agents.exploit_detector import ExploitDetectorAgent
        from agents.risk_scorer import RiskScorerAgent
        from agents.alert_generator import AlertGeneratorAgent
        from agents.report_writer import ReportWriterAgent
        from agents.historical_comparator import HistoricalComparatorAgent
        from agents.predictive_analyzer import PredictiveAnalyzerAgent
        
        pipeline_agents = {
            "bridge_monitor": BridgeMonitorAgent(self.config),
            "flow_analyzer": FlowAnalyzerAgent(self.config),
            "historical_comparator": HistoricalComparatorAgent(self.config),
            "anomaly_detector": AnomalyDetectorAgent(self.config),
            "exploit_detector": ExploitDetectorAgent(self.config),
            "risk_scorer": RiskScorerAgent(self.config),
            "predictive_analyzer": PredictiveAnalyzerAgent(self.config),
            "alert_generator": AlertGeneratorAgent(self.config),
            "report_writer": ReportWriterAgent(self.config),
        }
        
        # Define pipeline stages based on mode
        if mode == "monitor":
            stages = ["bridge_monitor"]
        elif mode == "analyze":
            stages = ["bridge_monitor", "flow_analyzer", "historical_comparator",
                      "anomaly_detector", "exploit_detector"]
        elif mode == "alerts":
            stages = ["bridge_monitor", "flow_analyzer", "anomaly_detector",
                      "exploit_detector", "risk_scorer", "alert_generator"]
        elif mode == "report":
            stages = ["bridge_monitor", "flow_analyzer", "historical_comparator",
                      "anomaly_detector", "exploit_detector", "risk_scorer",
                      "predictive_analyzer", "report_writer"]
        else:  # full
            stages = list(pipeline_agents.keys())
        
        for stage_name in stages:
            agent = pipeline_agents[stage_name]
            stage_start = time.time()
            try:
                logger.info("Running agent: %s", stage_name)
                result = agent.process(self.context)
                self.context[stage_name] = result
                elapsed = time.time() - stage_start
                self.context["pipeline_status"][stage_name] = {
                    "status": "success",
                    "elapsed_seconds": round(elapsed, 2),
                }
                self._results_cache[stage_name] = result
                logger.info("Agent %s completed in %.2fs", stage_name, elapsed)
            except Exception as e:
                logger.error("Agent %s failed: %s", stage_name, str(e))
                self.context["pipeline_status"][stage_name] = {
                    "status": "error",
                    "error": str(e),
                }
                self.context[stage_name] = {"error": str(e)}
        
        total_elapsed = time.time() - start_time
        self.context["total_elapsed_seconds"] = round(total_elapsed, 2)
        logger.info("Pipeline completed in %.2fs", total_elapsed)
        
        return self.context
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the last pipeline run."""
        return {
            "timestamp": self.context.get("timestamp"),
            "mode": self.context.get("mode"),
            "status": self.context.get("pipeline_status"),
            "total_elapsed": self.context.get("total_elapsed_seconds"),
            "alerts_count": len(self.context.get("alert_generator", {}).get("alerts", [])),
            "anomalies_count": len(self.context.get("anomaly_detector", {}).get("anomalies", [])),
            "exploits_count": len(self.context.get("exploit_detector", {}).get("exploits", [])),
        }
