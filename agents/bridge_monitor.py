"""
Bridge Monitor Agent
====================
Fetches live cross-chain bridge data from DeFiLlama API.
Monitors TVL, volume, and flow data across 15+ chains.

API Endpoints:
  - https://api.llama.fi/protocols (main endpoint - works!)
  - https://api.llama.fi/tvl/{protocol} (per-protocol TVL)

Token consumption: ~0 (HTTP calls only, no LLM inference)
Rate limits: DeFiLlama is generous; we add delays between bulk calls.
"""

import time
import logging
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("bridgeguard.agents.bridge_monitor")


class BridgeMonitorAgent:
    """
    Monitors cross-chain bridge activity using DeFiLlama public API.
    
    Fetches:
      - Bridge TVL per chain (aggregated from all bridge protocols)
      - Bridge protocols and their TVL
      - Chain-specific TVL breakdown
      - Protocol change metrics (1d, 7d)
    
    Token consumption: ~0 (HTTP calls only, no LLM inference)
    """
    
    # Map our chain names to DeFiLlama chain names
    CHAIN_NAME_MAP = {
        "Ethereum": "Ethereum",
        "Arbitrum": "Arbitrum",
        "Base": "Base",
        "Optimism": "Optimism",
        "Polygon": "Polygon",
        "BSC": "Binance",
        "Avalanche": "Avalanche",
        "Fantom": "Fantom",
        "zkSync": "zkSync Era",
        "Linea": "Linea",
        "Scroll": "Scroll",
        "Mantle": "Mantle",
        "Blast": "Blast",
        "Mode": "Mode",
        "Sei": "Sei",
    }
    
    def __init__(self, config=None):
        from core.config import BridgeGuardConfig
        self.config = config or BridgeGuardConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BridgeGuard/1.0 (cross-chain monitor)"
        })
        logger.info("BridgeMonitorAgent initialized")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch all bridge data and return structured results.
        
        Returns:
            {
                "bridges": [...],
                "chain_tvl": {chain: tvl},
                "chain_volume": {chain: volume},
                "top_bridges": [...],
                "total_tvl": float,
                "fetch_timestamp": str
            }
        """
        logger.info("Fetching bridge data from DeFiLlama...")
        
        result = {
            "bridges": [],
            "chain_tvl": {},
            "chain_volume": {},
            "top_bridges": [],
            "total_tvl": 0,
            "fetch_timestamp": datetime.utcnow().isoformat(),
            "chains_monitored": self.config.get_chain_names(),
        }
        
        # 1. Fetch all protocols from DeFiLlama
        protocols = self._fetch_protocols()
        if not protocols:
            logger.error("Failed to fetch any protocols from DeFiLlama")
            return result
        
        # 2. Filter to bridge protocols
        bridges = self._filter_bridges(protocols)
        result["bridges"] = bridges
        logger.info("Found %d bridge protocols", len(bridges))
        
        # 3. Extract top bridges by TVL
        result["top_bridges"] = self._extract_top_bridges(bridges)
        
        # 4. Compute chain-level TVL from bridge protocols
        result["chain_tvl"] = self._compute_chain_tvl(bridges)
        result["total_tvl"] = sum(result["chain_tvl"].values())
        
        # 5. Estimate daily volume from TVL and change metrics
        result["chain_volume"] = self._estimate_chain_volume(bridges)
        
        logger.info("Fetched data for %d bridges, total TVL: $%.2fM across %d chains",
                     len(result["bridges"]), result["total_tvl"] / 1e6, len(result["chain_tvl"]))
        return result
    
    def _fetch_protocols(self) -> List[Dict[str, Any]]:
        """Fetch all protocols from DeFiLlama."""
        url = "https://api.llama.fi/protocols"
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return []
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch protocols: %s", e)
            return []
    
    def _filter_bridges(self, protocols: List[Dict]) -> List[Dict]:
        """Filter protocols to only bridges."""
        bridges = []
        for p in protocols:
            category = p.get("category", "")
            if category == "Bridge" and p.get("tvl") is not None:
                bridges.append(p)
        return bridges
    
    def _extract_top_bridges(self, bridges: List[Dict]) -> List[Dict[str, Any]]:
        """Extract top bridges by TVL, sorted descending."""
        scored = []
        for p in bridges:
            tvl = p.get("tvl", 0) or 0
            if tvl > 0:
                scored.append({
                    "name": p.get("name", "unknown"),
                    "slug": p.get("slug", ""),
                    "tvl": tvl,
                    "chains": p.get("chains", []),
                    "category": p.get("category", "Bridge"),
                    "change_1d": p.get("change_1d", 0),
                    "change_7d": p.get("change_7d", 0),
                })
        
        scored.sort(key=lambda x: x["tvl"], reverse=True)
        return scored[:50]  # Top 50
    
    def _compute_chain_tvl(self, bridges: List[Dict]) -> Dict[str, float]:
        """Aggregate TVL by chain from all bridge protocols."""
        chain_tvl: Dict[str, float] = {}
        
        # Build reverse mapping: DeFiLlama chain name -> our chain name
        reverse_map = {}
        for our_name, llama_name in self.CHAIN_NAME_MAP.items():
            reverse_map[llama_name.lower()] = our_name
        
        for bridge in bridges:
            chain_tvls = bridge.get("chainTvls", {})
            if not isinstance(chain_tvls, dict):
                continue
            
            for chain_key, tvl_val in chain_tvls.items():
                if not isinstance(tvl_val, (int, float)):
                    continue
                
                # Try to map to our chain names
                normalized = chain_key.lower()
                mapped = reverse_map.get(normalized)
                
                if mapped:
                    chain_tvl[mapped] = chain_tvl.get(mapped, 0) + tvl_val
                else:
                    # Check partial matches
                    for llama_name, our_name in reverse_map.items():
                        if llama_name in normalized or normalized in llama_name:
                            chain_tvl[our_name] = chain_tvl.get(our_name, 0) + tvl_val
                            break
        
        return chain_tvl
    
    def _estimate_chain_volume(self, bridges: List[Dict]) -> Dict[str, float]:
        """
        Estimate daily volume per chain.
        Uses TVL * turnover ratio and 1d change as proxies.
        """
        chain_volume: Dict[str, float] = {}
        
        for bridge in bridges:
            chain_tvls = bridge.get("chainTvls", {})
            change_1d = bridge.get("change_1d", 0) or 0
            
            for chain_key, tvl_val in chain_tvls.items():
                if not isinstance(tvl_val, (int, float)) or tvl_val <= 0:
                    continue
                
                # Map chain name
                normalized = chain_key.lower()
                mapped_chain = None
                for llama_name, our_name in self.CHAIN_NAME_MAP.items():
                    if llama_name.lower() in normalized or normalized in llama_name.lower():
                        mapped_chain = our_name
                        break
                
                if not mapped_chain:
                    continue
                
                # Estimate volume: |change_1d| * TVL / some factor
                # Also add baseline turnover (bridges typically move 3-10% of TVL daily)
                estimated_daily = tvl_val * 0.05  # 5% baseline turnover
                change_volume = abs(change_1d) * tvl_val * 0.1  # change-based volume
                volume = estimated_daily + change_volume
                
                chain_volume[mapped_chain] = chain_volume.get(mapped_chain, 0) + volume
        
        return chain_volume
    
    def get_bridge_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up a specific bridge by name from last fetch."""
        for b in self._cache.get("bridges", []):
            if b.get("name", "").lower() == name.lower():
                return b
        return None
