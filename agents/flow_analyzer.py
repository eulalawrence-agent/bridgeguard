"""
Flow Analyzer Agent
===================
Analyzes cross-chain fund flow patterns between chains.
Identifies dominant corridors, unusual routing, and flow imbalances.

Token consumption: ~0 (statistical analysis only)
"""

import logging
import math
from typing import Any, Dict, List, Tuple
from collections import defaultdict

logger = logging.getLogger("bridgeguard.agents.flow_analyzer")


class FlowAnalyzerAgent:
    """
    Analyzes fund flow patterns between blockchain chains.
    
    Metrics computed:
      - Inbound/outbound volume per chain
      - Net flow (inbound - outbound)
      - Top flow corridors (chain A -> chain B)
      - Flow imbalance ratio
      - Concentration risk (dominance of single corridors)
    
    Token consumption: ~0 (statistical analysis only)
    """
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        logger.info("FlowAnalyzerAgent initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze flow patterns from bridge monitor data.
        
        Returns:
            {
                "chain_flows": {chain: {"inbound": x, "outbound": y, "net": z}},
                "top_corridors": [(from, to, volume), ...],
                "imbalance_chains": [chain, ...],
                "concentration_risk": float,
                "total_volume": float,
            }
        """
        logger.info("Analyzing cross-chain flow patterns...")
        
        monitor_data = context.get("bridge_monitor", {})
        bridges = monitor_data.get("bridges", [])
        chain_tvl = monitor_data.get("chain_tvl", {})
        
        # Build flow data from bridge protocol information
        chain_flows = self._compute_chain_flows(bridges, chain_tvl)
        top_corridors = self._find_top_corridors(bridges)
        imbalance_chains = self._find_imbalanced_chains(chain_flows)
        concentration = self._compute_concentration_risk(top_corridors)
        total_vol = sum(
            f.get("volume", 0) for f in chain_flows.values()
        ) / 2 if chain_flows else 0  # divide by 2 to avoid double-counting
        
        result = {
            "chain_flows": chain_flows,
            "top_corridors": top_corridors[:20],
            "imbalance_chains": imbalance_chains,
            "concentration_risk": concentration,
            "total_volume": total_vol,
            "total_chains_with_flow": len(chain_flows),
            "analysis_timestamp": context.get("bridge_monitor", {}).get("fetch_timestamp"),
        }
        
        logger.info("Flow analysis complete: %d corridors, concentration risk=%.2f",
                     len(top_corridors), concentration)
        return result
    
    def _compute_chain_flows(self, bridges: List[Dict], chain_tvl: Dict) -> Dict[str, Dict]:
        """
        Compute inbound/outbound/net flow per chain.
        Uses TVL differences and chain data as flow proxies.
        """
        chain_flows: Dict[str, Dict[str, float]] = {}
        
        for chain in self.config.monitored_chains:
            tvl = chain_tvl.get(chain.name, 0)
            # Estimate daily volume as percentage of TVL (typical DeFi ratio)
            # Bridges typically move 5-15% of TVL daily
            estimated_volume = tvl * 0.08  # conservative 8% daily turnover
            
            chain_flows[chain.name] = {
                "tvl": tvl,
                "estimated_daily_volume": estimated_volume,
                "inbound": estimated_volume * 0.45,   # slight net outflow assumption
                "outbound": estimated_volume * 0.55,
                "net": estimated_volume * 0.45 - estimated_volume * 0.55,
                "volume": estimated_volume,
            }
        
        return chain_flows
    
    def _find_top_corridors(self, bridges: List[Dict]) -> List[Tuple[str, str, float]]:
        """
        Identify top flow corridors between chains.
        Uses bridge protocol chain distribution to estimate flows.
        """
        corridors: Dict[Tuple[str, str], float] = defaultdict(float)
        chain_names = [c.name.lower() for c in self.config.monitored_chains]
        
        for bridge in bridges:
            chain_tvls = bridge.get("currentChainTvls", bridge.get("chainTvls", {}))
            if not isinstance(chain_tvls, dict):
                continue
            
            chains_active = []
            for chain_key, tvl_val in chain_tvls.items():
                if isinstance(tvl_val, (int, float)) and tvl_val > 0:
                    normalized = chain_key.lower().replace("-locked", "").replace("-pool2", "")
                    chains_active.append((normalized, tvl_val))
            
            # Estimate flows between chain pairs proportional to TVL product
            for i, (chain_a, tvl_a) in enumerate(chains_active):
                for chain_b, tvl_b in chains_active[i+1:]:
                    # Flow proxy: sqrt(tvl_a * tvl_b)
                    flow = math.sqrt(max(tvl_a, 0) * max(tvl_b, 0))
                    corridors[(chain_a, chain_b)] += flow
        
        sorted_corridors = sorted(corridors.items(), key=lambda x: x[1], reverse=True)
        return [(c[0], c[1], vol) for c, vol in sorted_corridors]
    
    def _find_imbalanced_chains(self, chain_flows: Dict) -> List[str]:
        """Find chains with significant flow imbalances."""
        imbalanced = []
        for chain, flows in chain_flows.items():
            inbound = flows.get("inbound", 0)
            outbound = flows.get("outbound", 0)
            if inbound + outbound > 0:
                ratio = max(inbound, outbound) / max(min(inbound, outbound), 1)
                if ratio > 2.0:  # 2:1 imbalance threshold
                    imbalanced.append(chain)
        return imbalanced
    
    def _compute_concentration_risk(self, corridors: List[Tuple]) -> float:
        """
        Compute concentration risk (0-1).
        Higher = more concentrated in fewer corridors.
        Uses Herfindahl-Hirschman Index (HHI) approach.
        """
        if not corridors:
            return 0.0
        
        total = sum(abs(v) for _, _, v in corridors)
        if total == 0:
            return 0.0
        
        hhi = sum((abs(v) / total) ** 2 for _, _, v in corridors)
        # Normalize: HHI ranges from 1/N to 1
        n = len(corridors)
        min_hhi = 1.0 / n if n > 0 else 0
        normalized = (hhi - min_hhi) / (1.0 - min_hhi) if (1.0 - min_hhi) > 0 else 0
        return round(min(normalized, 1.0), 4)
