#!/usr/bin/env python3
"""BridgeGuard - Cross-chain bridge monitoring and exploit detection system."""

from agents.bridge_monitor import BridgeMonitorAgent
from agents.flow_analyzer import FlowAnalyzerAgent
from agents.anomaly_detector import AnomalyDetectorAgent
from agents.exploit_detector import ExploitDetectorAgent
from agents.risk_scorer import RiskScorerAgent
from agents.alert_generator import AlertGeneratorAgent
from agents.report_writer import ReportWriterAgent
from agents.historical_comparator import HistoricalComparatorAgent
from agents.predictive_analyzer import PredictiveAnalyzerAgent
from core.orchestrator import Orchestrator
from core.config import BridgeGuardConfig

__version__ = "1.0.0"
