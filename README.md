# BridgeGuard 🌉

**AI-powered cross-chain bridge monitoring, anomaly detection, and risk scoring.**

BridgeGuard is a real-time monitoring system that watches 15+ blockchain bridges across major ecosystems, detects suspicious activity and potential exploits, tracks fund flows between chains, and generates risk scores — all powered by a team of 9 specialized AI agents processing 87M+ tokens per day.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BridgeGuard Pipeline                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐   │
│  │  DeFiLlama   │───▶│         Data Ingestion Layer              │   │
│  │  API (Free)  │    │  (Bridge TVL · Volume · Chain Flows)      │   │
│  └──────────────┘    └────────────────┬─────────────────────────┘   │
│                                       │                             │
│                        ┌──────────────▼──────────────┐              │
│                        │    9 Specialized AI Agents   │              │
│                        │      87M+ tokens/day         │              │
│                        ├──────────────────────────────┤              │
│                        │                              │              │
│   ┌────────────────────┼──────────────────────────┐   │              │
│   │                    │                          │   │              │
│   ▼                    ▼                          ▼   │              │
│ ┌──────────┐  ┌────────────────┐  ┌───────────────┐  │              │
│ │ Data     │  │ Anomaly        │  │ Fund Flow     │  │              │
│ │ Collector│  │ Detector       │  │ Tracker       │  │              │
│ │ Agent    │  │ Agent          │  │ Agent         │  │              │
│ └──────────┘  └────────────────┘  └───────────────┘  │              │
│   ┌──────────────────────────────────────────────────┐│              │
│   │                                                  ││              │
│   ▼                    ▼                          ▼  ││              │
│ ┌──────────┐  ┌────────────────┐  ┌───────────────┐  ││              │
│ │ Risk     │  │ Exploit        │  │ Chain         │  ││              │
│ │ Scorer   │  │ Pattern        │  │ Correlation   │  ││              │
│ │ Agent    │  │ Agent          │  │ Agent         │  ││              │
│ └──────────┘  └────────────────┘  └───────────────┘  ││              │
│   ┌──────────────────────────────────────────────────┐││              │
│   │                                                  │││              │
│   ▼                    ▼                          ▼  │││              │
│ ┌──────────┐  ┌────────────────┐  ┌───────────────┐  │││              │
│ │ Alert    │  │ Narrative      │  │ Forecasting   │  │││              │
│ │ Generator│  │ Synthesizer    │  │ Agent         │  │││              │
│ │ Agent    │  │ Agent          │  │               │  │││              │
│ └──────────┘  └────────────────┘  └───────────────┘  │││              │
│                                                      │││              │
│                        ┌─────────────────┐           │││              │
│                        │  Alert Output   │◀──────────┘┘│              │
│                        │  (Webhook/TG/   │◀────────────┘              │
│                        │   Slack/Discord)│◀──────────────             │
│                        └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Real-time bridge monitoring** across 15+ supported chains and bridges
- **Anomaly detection** using statistical and AI-driven analysis on TVL, volume, and flow patterns
- **Fund flow tracking** — follow assets as they move across bridges and chains
- **Risk scoring** — every bridge and transaction receives a dynamic 0–100 risk score
- **Exploit pattern recognition** — trained on historical bridge hacks (Ronin, Wormhole, Harmony, Nomad, etc.)
- **Chain correlation engine** — identifies coordinated suspicious activity across multiple chains
- **Multi-channel alerts** — webhook, Telegram, Slack, Discord, email
- **87M+ tokens/day** of AI inference across 9 specialized agents
- **DeFiLlama-powered** — free, open API data; no paid API keys required

## Supported Chains

| Chain | Bridges Monitored |
|-------|-------------------|
| Ethereum | Arbitrum, Optimism, Base, zkSync, Starknet, Linea |
| BNB Chain | Multichain, Stargate, Celer |
| Avalanche | Multichain, Platypus, Stargate |
| Polygon | PoS Bridge, Matic Bridge |
| Arbitrum | Stargate, Hop, Across |
| Optimism | Synapse, Hop, Across |
| Base | Stargate, Across |
| zkSync | Orbiter, LayerZero |
| Starknet | StarkGate |
| Solana | Wormhole, Allbridge, Socket |
| Fantom | Multichain, SpookySwap Bridge |
| Gnosis | Omnibridge, Multichain |
| Tron | BitTorrent Chain |
| Bittensor | Bittensor Bridge |
| Cosmos (IBC) | Axelar, Gravity Bridge |

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/bridgeguard.git
cd bridgeguard

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your alert endpoints

# Run
python -m bridgeguard --config config.yaml
```

### Requirements

- Python 3.10+
- 16 GB RAM (recommended for full agent stack)
- Internet access (DeFiLlama API, on-chain RPCs)

## Usage

```bash
# Start the full monitoring pipeline
bridgeguard start --config config.yaml

# Monitor a specific bridge
bridgeguard monitor --bridge wormhole --chains solana,ethereum

# Run a one-shot risk assessment on all bridges
bridgeguard risk-scan

# View live fund flows
bridgeguard flows --min-amount 100000 --token USDC

# Generate a report
bridgeguard report --period 24h --format markdown --output report.md

# List active agents and their token consumption
bridgeguard agents --stats

# Dry-run mode (no alerts, just log)
bridgeguard start --dry-run
```

## Agent Descriptions

| # | Agent | Role | Tokens/Day | Description |
|---|-------|------|------------|-------------|
| 1 | **Data Collector** | Ingestion | ~12M | Pulls TVL, volume, and flow data from DeFiLlama and on-chain RPCs every 60s |
| 2 | **Anomaly Detector** | Analysis | ~8M | Runs statistical models (z-score, IQR, LSTM) to flag deviations from baseline |
| 3 | **Fund Flow Tracker** | Tracing | ~10M | Traces asset movements across bridge endpoints, builds flow graphs |
| 4 | **Risk Scorer** | Scoring | ~6M | Computes composite risk scores (0–100) from TVL changes, volume spikes, delay patterns |
| 5 | **Exploit Pattern Agent** | Detection | ~14M | Matches current activity against known exploit signatures and novel attack vectors |
| 6 | **Chain Correlation Agent** | Cross-chain | ~8M | Identifies coordinated suspicious activity across multiple chains simultaneously |
| 7 | **Alert Generator** | Notification | ~4M | Filters, deduplicates, and formats alerts for delivery via configured channels |
| 8 | **Narrative Synthesizer** | Reporting | ~15M | Generates human-readable threat narratives explaining what happened and why |
| 9 | **Forecasting Agent** | Prediction | ~10M | Predicts near-term risk trajectory based on historical patterns and current trends |
| | **Total** | | **~87M** | |

## API & Data Sources

| Source | Type | Cost | Usage |
|--------|------|------|-------|
| [DeFiLlama](https://defillama.com/) | REST API | Free | Primary data source for bridge TVL, volume, and chain metrics |
| On-chain RPCs | JSON-RPC | Free tier | Direct blockchain queries for transaction-level tracing |

BridgeGuard is built entirely on free data sources. No paid API keys are required.

## Configuration

```yaml
# config.yaml
monitoring:
  interval_seconds: 60
  bridges: [wormhole, stargate, hop, across, multichain, allbridge, ...]

agents:
  max_tokens_per_day: 90_000_000
  concurrency: 9

risk:
  alert_threshold: 70
  critical_threshold: 90

alerts:
  channels:
    - type: webhook
      url: https://your-webhook.example.com
    - type: telegram
      bot_token: "YOUR_BOT_TOKEN"
      chat_id: "YOUR_CHAT_ID"
    - type: slack
      webhook_url: "https://hooks.slack.com/..."
```

## License

MIT License. See [LICENSE](LICENSE) for details.
