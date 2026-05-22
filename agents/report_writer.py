"""
Report Writer Agent
===================
Generates formatted reports with statistics, tables, and colored output.
Supports daily and weekly report formats.

Token consumption: ~0 (formatting only)
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.report_writer")


class ReportWriterAgent:
    """
    Generates formatted reports from pipeline data.
    
    Report sections:
      - Executive Summary
      - Chain TVL Overview
      - Bridge Rankings
      - Flow Analysis
      - Anomaly Report
      - Exploit Risk Assessment
      - Risk Scores
      - Alert Summary
    
    Token consumption: ~0 (formatting only)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        logger.info("ReportWriterAgent initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete report from pipeline data.
        
        Returns:
            {
                "report_sections": [...],
                "console_output": str,
                "report_text": str,
            }
        """
        logger.info("Generating report...")
        
        sections = []
        
        # Executive Summary
        sections.append(self._executive_summary(context))
        
        # Chain TVL Overview
        sections.append(self._chain_tvl_overview(context))
        
        # Top Bridges
        sections.append(self._top_bridges(context))
        
        # Flow Analysis
        sections.append(self._flow_analysis(context))
        
        # Anomaly Report
        sections.append(self._anomaly_report(context))
        
        # Exploit Risk
        sections.append(self._exploit_risk(context))
        
        # Risk Scores
        sections.append(self._risk_scores(context))
        
        # Alert Summary
        sections.append(self._alert_summary(context))
        
        # Build text report
        report_text = "\n\n".join(s["text"] for s in sections)
        
        result = {
            "report_sections": sections,
            "report_text": report_text,
            "section_count": len(sections),
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        logger.info("Report generated with %d sections", len(sections))
        return result
    
    def _executive_summary(self, ctx: Dict) -> Dict:
        """High-level summary of bridge status."""
        monitor = ctx.get("bridge_monitor", {})
        anomaly = ctx.get("anomaly_detector", {})
        exploit = ctx.get("exploit_detector", {})
        risk = ctx.get("risk_scorer", {})
        alerts = ctx.get("alert_generator", {})
        
        total_tvl = monitor.get("total_tvl", 0)
        num_bridges = len(monitor.get("bridges", []))
        num_anomalies = anomaly.get("total_anomalies", 0)
        exploit_risk = exploit.get("exploit_risk_score", 0)
        overall_risk = risk.get("overall_risk", 0)
        alert_counts = alerts.get("alert_counts", {})
        
        text = f"""═══════════════════════════════════════════════════════════════
  🛡️  BridgeGuard Report — Executive Summary
═══════════════════════════════════════════════════════════════

  📅 Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
  🔗 Bridges Monitored: {num_bridges}
  💰 Total Bridge TVL: ${total_tvl/1e9:.2f}B
  ⚠️  Anomalies Detected: {num_anomalies}
  🔓 Exploit Risk Score: {exploit_risk}/100
  📊 Overall Risk Score: {overall_risk}/100 ({risk.get('risk_grade', 'N/A')})
  🚨 Alerts: {sum(alert_counts.values())} total (🔴{alert_counts.get('critical', 0)} 🟡{alert_counts.get('warning', 0)} 🔵{alert_counts.get('info', 0)})"""
        
        return {"title": "Executive Summary", "text": text}
    
    def _chain_tvl_overview(self, ctx: Dict) -> Dict:
        """TVL breakdown by chain."""
        monitor = ctx.get("bridge_monitor", {})
        chain_tvl = monitor.get("chain_tvl", {})
        
        if not chain_tvl:
            return {"title": "Chain TVL Overview", "text": "No TVL data available."}
        
        total = sum(chain_tvl.values())
        sorted_chains = sorted(chain_tvl.items(), key=lambda x: x[1], reverse=True)
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  📊 Chain TVL Overview",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  {'Chain':<15} {'TVL':>15} {'Share':>8}  {'Bar'}",
            "  " + "─" * 55,
        ]
        
        for chain, tvl in sorted_chains:
            if tvl <= 0:
                continue
            share = (tvl / total * 100) if total > 0 else 0
            bar_len = int(share / 2)
            bar = "█" * bar_len + "░" * (25 - bar_len)
            
            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.1f}M"
            elif tvl >= 1e3:
                tvl_str = f"${tvl/1e3:.0f}K"
            else:
                tvl_str = f"${tvl:.0f}"
            
            lines.append(f"  {chain:<15} {tvl_str:>15} {share:>6.1f}%  {bar}")
        
        lines.append(f"\n  {'TOTAL':<15} ${total/1e9:.2f}B")
        
        return {"title": "Chain TVL Overview", "text": "\n".join(lines)}
    
    def _top_bridges(self, ctx: Dict) -> Dict:
        """Top bridges by TVL."""
        monitor = ctx.get("bridge_monitor", {})
        bridges = monitor.get("top_bridges", [])
        
        if not bridges:
            return {"title": "Top Bridges", "text": "No bridge data available."}
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  🌉 Top Bridges by TVL",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  {'#':<4} {'Bridge':<25} {'TVL':>15} {'Chains':>6}",
            "  " + "─" * 55,
        ]
        
        for i, bridge in enumerate(bridges[:15], 1):
            name = bridge.get("name", "unknown")[:24]
            tvl = bridge.get("tvl", 0)
            num_chains = len(bridge.get("chains", []))
            
            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.1f}M"
            else:
                tvl_str = f"${tvl/1e3:.0f}K"
            
            lines.append(f"  {i:<4} {name:<25} {tvl_str:>15} {num_chains:>5}")
        
        return {"title": "Top Bridges", "text": "\n".join(lines)}
    
    def _flow_analysis(self, ctx: Dict) -> Dict:
        """Flow analysis summary."""
        flow = ctx.get("flow_analyzer", {})
        corridors = flow.get("top_corridors", [])
        concentration = flow.get("concentration_risk", 0)
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  🔄 Flow Analysis",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  Concentration Risk: {concentration:.2%}",
            f"  Active Corridors: {len(corridors)}",
            "",
            "  Top Flow Corridors:",
            "  " + "─" * 45,
        ]
        
        for i, (src, dst, vol) in enumerate(corridors[:10], 1):
            vol_str = f"${vol/1e6:.1f}M" if vol >= 1e6 else f"${vol/1e3:.0f}K"
            lines.append(f"  {i:<3} {src:<15} → {dst:<15} {vol_str:>10}")
        
        if not corridors:
            lines.append("  No corridor data available.")
        
        return {"title": "Flow Analysis", "text": "\n".join(lines)}
    
    def _anomaly_report(self, ctx: Dict) -> Dict:
        """Anomaly report."""
        anomaly = ctx.get("anomaly_detector", {})
        anomalies = anomaly.get("anomalies", [])
        summary = anomaly.get("anomaly_summary", {})
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  ⚠️  Anomaly Report",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  Total Anomalies: {len(anomalies)}",
            f"  🔴 Critical: {summary.get('critical', 0)}",
            f"  🟡 Warning:  {summary.get('warning', 0)}",
            f"  🔵 Info:     {summary.get('info', 0)}",
            "",
        ]
        
        critical = [a for a in anomalies if a.get("severity") == "critical"]
        if critical:
            lines.append("  Critical Anomalies:")
            lines.append("  " + "─" * 45)
            for a in critical[:10]:
                lines.append(f"  • [{a.get('type', 'unknown')}] {a.get('description', 'N/A')}")
        
        warnings = [a for a in anomalies if a.get("severity") == "warning"]
        if warnings:
            lines.append("\n  Warnings:")
            lines.append("  " + "─" * 45)
            for a in warnings[:10]:
                lines.append(f"  • [{a.get('type', 'unknown')}] {a.get('description', 'N/A')}")
        
        if not anomalies:
            lines.append("  ✅ No anomalies detected.")
        
        return {"title": "Anomaly Report", "text": "\n".join(lines)}
    
    def _exploit_risk(self, ctx: Dict) -> Dict:
        """Exploit risk assessment."""
        exploit = ctx.get("exploit_detector", {})
        exploits = exploit.get("exploits", [])
        risk_score = exploit.get("exploit_risk_score", 0)
        high_risk = exploit.get("high_risk_bridges", [])
        
        risk_emoji = "🔴" if risk_score >= 70 else "🟡" if risk_score >= 40 else "🟢"
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  🔓 Exploit Risk Assessment",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  {risk_emoji} Exploit Risk Score: {risk_score}/100",
            f"  Potential Exploits: {len(exploits)}",
            f"  High-Risk Bridges: {len(high_risk)}",
            "",
        ]
        
        if high_risk:
            lines.append("  High-Risk Bridges:")
            lines.append("  " + "─" * 45)
            for b in high_risk:
                lines.append(f"  • {b['name']} (flags: {b['flag_count']}, level: {b['risk_level']})")
        
        if exploits:
            lines.append("\n  Exploit Indicators:")
            lines.append("  " + "─" * 45)
            for e in exploits[:10]:
                conf = e.get("confidence", 0)
                lines.append(f"  • [{e['type']}] conf={conf:.0%} — {e.get('description', 'N/A')}")
                if e.get("mitigation"):
                    lines.append(f"    → Mitigation: {e['mitigation']}")
        
        if not exploits:
            lines.append("  ✅ No exploit indicators detected.")
        
        return {"title": "Exploit Risk Assessment", "text": "\n".join(lines)}
    
    def _risk_scores(self, ctx: Dict) -> Dict:
        """Chain risk scores."""
        risk = ctx.get("risk_scorer", {})
        chain_scores = risk.get("chain_scores", {})
        
        if not chain_scores:
            return {"title": "Risk Scores", "text": "No risk score data available."}
        
        sorted_scores = sorted(chain_scores.items(), key=lambda x: x[1].get("score", 0))
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  📊 Chain Risk Scores",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"  {'Chain':<15} {'Score':>6} {'Grade':>6} {'TVL':>12}",
            "  " + "─" * 45,
        ]
        
        for chain, data in sorted_scores:
            score = data.get("score", 0)
            grade = data.get("grade", "N/A")
            tvl = data.get("tvl", 0)
            
            grade_emoji = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🟠", "F": "🔴"}.get(grade, "⚪")
            
            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.1f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.0f}M"
            else:
                tvl_str = f"${tvl/1e3:.0f}K"
            
            lines.append(f"  {chain:<15} {score:>5.1f} {grade_emoji} {grade}  {tvl_str:>12}")
        
        return {"title": "Risk Scores", "text": "\n".join(lines)}
    
    def _alert_summary(self, ctx: Dict) -> Dict:
        """Alert summary section."""
        alerts = ctx.get("alert_generator", {})
        alert_list = alerts.get("alerts", [])
        
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "  🚨 Alert Summary",
            "═══════════════════════════════════════════════════════════════",
            "",
        ]
        
        if not alert_list:
            lines.append("  ✅ No alerts — all systems nominal.")
        else:
            for alert in alert_list[:15]:
                sev_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    alert.get("severity", "info"), "⚪")
                lines.append(f"  {sev_emoji} [{alert.get('id', '???')}] {alert.get('title', 'Alert')}")
                if alert.get("chain") and alert.get("chain") != "SYSTEM":
                    lines.append(f"     Chain: {alert['chain']}")
                if alert.get("description"):
                    lines.append(f"     {alert['description'][:80]}")
                lines.append("")
        
        return {"title": "Alert Summary", "text": "\n".join(lines)}
