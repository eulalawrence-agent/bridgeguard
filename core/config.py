"""
BridgeGuard Configuration
=========================
Central configuration for all agents and thresholds.
Token consumption: ~0 (config only, no API calls)
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class APIEndpoints:
    """DeFiLlama API endpoints (no API key required)."""
    bridges_v1: str = "https://api.llama.fi/bridges"
    bridges_v2: str = "https://api.llama.fi/v2/bridges"
    bridge_protocols: str = "https://bridges.llama.fi/protocols"
    bridge_volume_chart: str = "https://api.llama.fi/v2/historicalChainTvl"
    defillama_tvl: str = "https://api.llama.fi/tvl/{protocol}"


@dataclass
class ChainConfig:
    """Configuration for a monitored blockchain."""
    name: str
    slug: str
    short_name: str
    min_tvl_alert: float = 50_000_000  # $50M minimum TVL to flag
    color: str = "white"


@dataclass
class ThresholdConfig:
    """Statistical thresholds for anomaly detection."""
    volume_spike_multiplier: float = 3.0       # 3x normal volume
    sudden_outflow_multiplier: float = 5.0     # 5x normal outflow
    tvl_drop_percentage: float = 20.0          # 20% TVL drop
    risk_score_critical: float = 80.0          # Score >= 80 = critical
    risk_score_warning: float = 60.0           # Score >= 60 = warning
    anomaly_z_score_threshold: float = 2.5     # Z-score for anomaly
    exploit_volume_threshold: float = 100_000_000  # $100M sudden movement
    low_volume_threshold: float = 10_000       # Suspiciously low volume


@dataclass
class BridgeGuardConfig:
    """Main configuration for BridgeGuard."""
    api: APIEndpoints = field(default_factory=APIEndpoints)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    
    monitored_chains: List[ChainConfig] = field(default_factory=lambda: [
        ChainConfig("Ethereum",   "ethereum",  "ETH",  color="blue"),
        ChainConfig("Arbitrum",   "arbitrum",  "ARB",  color="cyan"),
        ChainConfig("Base",       "base",      "BASE", color="blue"),
        ChainConfig("Optimism",   "optimism",  "OP",   color="red"),
        ChainConfig("Polygon",    "polygon",   "MATIC",color="purple"),
        ChainConfig("BSC",        "bsc",       "BSC",  color="yellow"),
        ChainConfig("Avalanche",  "avax",      "AVAX", color="red"),
        ChainConfig("Fantom",     "fantom",    "FTM",  color="blue"),
        ChainConfig("zkSync",     "era",       "zKS",  color="purple"),
        ChainConfig("Linea",      "linea",     "LNA",  color="green"),
        ChainConfig("Scroll",     "scroll",    "SCR",  color="cyan"),
        ChainConfig("Mantle",     "mantle",    "MNT",  color="yellow"),
        ChainConfig("Blast",      "blast",     "BLST", color="blue"),
        ChainConfig("Mode",       "mode",      "MODE", color="purple"),
        ChainConfig("Sei",        "sei",       "SEI",  color="blue"),
    ])
    
    # Chain name -> slug mapping for API responses
    chain_slugs: Dict[str, str] = field(default_factory=lambda: {
        "ethereum":  "ethereum",
        "arbitrum":  "arbitrum",
        "base":      "base",
        "optimism":  "optimism",
        "polygon":   "polygon",
        "bsc":       "bsc",
        "avax":      "avax",
        "fantom":    "fantom",
        "era":       "era",
        "linea":     "linea",
        "scroll":    "scroll",
        "mantle":    "mantle",
        "blast":     "blast",
        "mode":      "mode",
        "sei":       "sei",
    })
    
    request_timeout: int = 30
    max_retries: int = 3
    data_dir: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    ))
    cache_ttl_seconds: int = 300  # 5 minutes
    
    def get_chain_by_name(self, name: str) -> Optional[ChainConfig]:
        """Get chain config by name (case-insensitive)."""
        for chain in self.monitored_chains:
            if chain.name.lower() == name.lower():
                return chain
        return None
    
    def get_chain_names(self) -> List[str]:
        """Return list of all monitored chain names."""
        return [c.name for c in self.monitored_chains]
    
    def get_chain_slugs(self) -> List[str]:
        """Return list of all chain slugs."""
        return [c.slug for c in self.monitored_chains]
