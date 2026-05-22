#!/usr/bin/env python3
"""
BridgeGuard CLI
===============
Cross-chain bridge monitoring and exploit detection system.

Usage:
    python cli.py monitor          - Fetch live bridge data
    python cli.py analyze          - Full analysis pipeline
    python cli.py report           - Generate comprehensive report
    python cli.py alerts           - Show alerts for suspicious activity
    python cli.py chains           - List monitored chains
    python cli.py status           - Show system status

No API keys required — uses public DeFiLlama API.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Ensure we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging for the tool."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def print_banner():
    """Print the BridgeGuard banner."""
    banner = """
[bold blue]
 ╔═══════════════════════════════════════════════════════════╗
 ║   🛡️  BridgeGuard — Cross-Chain Bridge Monitor           ║
 ║   Monitoring 15+ chains • Real-time DeFiLlama data       ║
 ╚═══════════════════════════════════════════════════════════╝
[/bold blue]"""
    console.print(banner)


def cmd_monitor():
    """Fetch live bridge data."""
    from core.orchestrator import Orchestrator
    
    console.print("\n[bold cyan]🔍 Fetching live bridge data...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Connecting to DeFiLlama API...", total=None)
        
        orchestrator = Orchestrator()
        results = orchestrator.run_pipeline(mode="monitor")
        
        progress.update(task, description="Data fetched successfully!")
    
    # Display results
    monitor = results.get("bridge_monitor", {})
    total_tvl = monitor.get("total_tvl", 0)
    num_bridges = len(monitor.get("bridges", []))
    chain_tvl = monitor.get("chain_tvl", {})
    
    console.print(Panel(
        f"[bold green]✅ Data fetched successfully![/bold green]\n\n"
        f"🔗 Bridges found: {num_bridges}\n"
        f"💰 Total TVL: ${total_tvl/1e9:.2f}B\n"
        f"⛓️  Chains with data: {len(chain_tvl)}\n"
        f"⏱️  Elapsed: {results.get('total_elapsed_seconds', 0):.1f}s",
        title="Monitor Results",
        border_style="green",
    ))
    
    # TVL Table
    if chain_tvl:
        table = Table(title="Chain TVL Overview", box=box.ROUNDED)
        table.add_column("Chain", style="cyan bold")
        table.add_column("TVL", justify="right", style="green")
        table.add_column("Share", justify="right", style="yellow")
        table.add_column("Status", justify="center")
        
        sorted_tvl = sorted(chain_tvl.items(), key=lambda x: x[1], reverse=True)
        for chain, tvl in sorted_tvl:
            if tvl <= 0:
                continue
            share = (tvl / total_tvl * 100) if total_tvl > 0 else 0
            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.1f}M"
            elif tvl >= 1e3:
                tvl_str = f"${tvl/1e3:.0f}K"
            else:
                tvl_str = f"${tvl:.0f}"
            
            status = "🟢" if share > 5 else "🟡" if share > 1 else "⚪"
            table.add_row(chain, tvl_str, f"{share:.1f}%", status)
        
        console.print(table)
    
    # Top Bridges
    top_bridges = monitor.get("top_bridges", [])
    if top_bridges:
        bridge_table = Table(title="Top 15 Bridges by TVL", box=box.ROUNDED)
        bridge_table.add_column("#", style="dim")
        bridge_table.add_column("Bridge", style="bold")
        bridge_table.add_column("TVL", justify="right", style="green")
        bridge_table.add_column("Chains", justify="center")
        
        for i, b in enumerate(top_bridges[:15], 1):
            tvl = b.get("tvl", 0)
            if tvl >= 1e9:
                tvl_str = f"${tvl/1e9:.2f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl/1e6:.1f}M"
            else:
                tvl_str = f"${tvl/1e3:.0f}K"
            
            bridge_table.add_row(
                str(i), b.get("name", "?")[:30], tvl_str,
                str(len(b.get("chains", [])))
            )
        
        console.print(bridge_table)


def cmd_analyze():
    """Run full analysis pipeline."""
    from core.orchestrator import Orchestrator
    
    console.print("\n[bold cyan]🔬 Running full analysis pipeline...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching data...", total=None)
        
        orchestrator = Orchestrator()
        
        progress.update(task, description="Analyzing flows...")
        results = orchestrator.run_pipeline(mode="analyze")
        
        progress.update(task, description="Analysis complete!")
    
    # Show anomaly results
    anomaly = results.get("anomaly_detector", {})
    anomalies = anomaly.get("anomalies", [])
    summary = anomaly.get("anomaly_summary", {})
    
    console.print(Panel(
        f"[bold]Anomaly Detection Results[/bold]\n\n"
        f"Total anomalies: {len(anomalies)}\n"
        f"🔴 Critical: {summary.get('critical', 0)}\n"
        f"🟡 Warning: {summary.get('warning', 0)}\n"
        f"🔵 Info: {summary.get('info', 0)}",
        title="Analysis Results",
        border_style="cyan",
    ))
    
    # Show exploit results
    exploit = results.get("exploit_detector", {})
    exploits = exploit.get("exploits", [])
    risk_score = exploit.get("exploit_risk_score", 0)
    
    risk_color = "red" if risk_score > 70 else "yellow" if risk_score > 40 else "green"
    console.print(Panel(
        f"[bold {risk_color}]Exploit Risk Score: {risk_score}/100[/bold {risk_color}]\n\n"
        f"Potential exploits detected: {len(exploits)}\n"
        f"High-risk bridges: {len(exploit.get('high_risk_bridges', []))}",
        title="Exploit Detection",
        border_style=risk_color,
    ))
    
    # Anomaly details
    if anomalies:
        table = Table(title="Detected Anomalies", box=box.ROUNDED)
        table.add_column("Type", style="bold")
        table.add_column("Chain/Bridge", style="cyan")
        table.add_column("Severity")
        table.add_column("Description", max_width=50)
        
        for a in anomalies[:20]:
            sev = a.get("severity", "info")
            sev_style = {"critical": "bold red", "warning": "bold yellow", "info": "blue"}.get(sev, "white")
            table.add_row(
                a.get("type", "?").replace("_", " ").title(),
                a.get("chain") or a.get("bridge") or "N/A",
                f"[{sev_style}]{sev.upper()}[/{sev_style}]",
                a.get("description", "")[:50],
            )
        
        console.print(table)


def cmd_report():
    """Generate comprehensive report."""
    from core.orchestrator import Orchestrator
    
    console.print("\n[bold cyan]📊 Generating comprehensive report...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running full pipeline...", total=None)
        
        orchestrator = Orchestrator()
        results = orchestrator.run_pipeline(mode="report")
        
        progress.update(task, description="Report generated!")
    
    # Print the report
    report = results.get("report_writer", {})
    report_text = report.get("report_text", "")
    
    if report_text:
        console.print(Panel(report_text, title="BridgeGuard Report", border_style="blue", expand=True))
    else:
        console.print("[yellow]No report data available.[/yellow]")
    
    # Summary
    summary = orchestrator.get_summary()
    console.print(Panel(
        f"Pipeline completed in {summary.get('total_elapsed', 0):.1f}s\n"
        f"Anomalies: {summary.get('anomalies_count', 0)} | "
        f"Exploits: {summary.get('exploits_count', 0)} | "
        f"Alerts: {summary.get('alerts_count', 0)}",
        title="Pipeline Summary",
        border_style="dim",
    ))


def cmd_alerts():
    """Show alerts for suspicious activity."""
    from core.orchestrator import Orchestrator
    
    console.print("\n[bold cyan]🚨 Checking for alerts...[/bold cyan]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing bridge data...", total=None)
        
        orchestrator = Orchestrator()
        results = orchestrator.run_pipeline(mode="alerts")
        
        progress.update(task, description="Alert check complete!")
    
    alerts_data = results.get("alert_generator", {})
    alerts = alerts_data.get("alerts", [])
    counts = alerts_data.get("alert_counts", {})
    
    # Summary panel
    total = sum(counts.values())
    if total == 0:
        console.print(Panel(
            "[bold green]✅ No alerts — all systems nominal![/bold green]\n\n"
            "No critical, warning, or informational alerts detected.",
            title="Alert Status",
            border_style="green",
        ))
        return
    
    console.print(Panel(
        f"[bold]Alert Summary[/bold]\n\n"
        f"Total alerts: {total}\n"
        f"🔴 Critical: {counts.get('critical', 0)}\n"
        f"🟡 Warning: {counts.get('warning', 0)}\n"
        f"🔵 Info: {counts.get('info', 0)}",
        title="🚨 Alert Status",
        border_style="red" if counts.get("critical", 0) > 0 else "yellow" if counts.get("warning", 0) > 0 else "green",
    ))
    
    # Alert table
    if alerts:
        table = Table(title="Active Alerts", box=box.ROUNDED)
        table.add_column("ID", style="dim")
        table.add_column("Type", style="bold")
        table.add_column("Severity")
        table.add_column("Chain")
        table.add_column("Title", max_width=40)
        
        for alert in alerts[:25]:
            sev = alert.get("severity", "info")
            sev_style = {"critical": "bold red", "warning": "bold yellow", "info": "blue"}.get(sev, "white")
            table.add_row(
                alert.get("id", "???"),
                alert.get("type", "?"),
                f"[{sev_style}]{sev.upper()}[/{sev_style}]",
                alert.get("chain", "N/A"),
                alert.get("title", "")[:40],
            )
        
        console.print(table)


def cmd_chains():
    """List all monitored chains."""
    from core.config import BridgeGuardConfig
    
    config = BridgeGuardConfig()
    
    table = Table(title="Monitored Chains", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Chain", style="bold cyan")
    table.add_column("Slug", style="dim")
    table.add_column("Short", style="yellow")
    table.add_column("Min TVL Alert", justify="right", style="green")
    
    for i, chain in enumerate(config.monitored_chains, 1):
        table.add_row(
            str(i),
            chain.name,
            chain.slug,
            chain.short_name,
            f"${chain.min_tvl_alert/1e6:.0f}M",
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(config.monitored_chains)} chains[/dim]")


def cmd_status():
    """Show system status."""
    from core.config import BridgeGuardConfig
    
    config = BridgeGuardConfig()
    
    console.print(Panel(
        f"[bold]BridgeGuard Status[/bold]\n\n"
        f"Version: 1.0.0\n"
        f"Monitored chains: {len(config.monitored_chains)}\n"
        f"API endpoints configured: {len(vars(config.api))}\n"
        f"Data directory: {config.data_dir}\n"
        f"Cache TTL: {config.cache_ttl_seconds}s\n"
        f"Request timeout: {config.request_timeout}s\n"
        f"Max retries: {config.max_retries}",
        title="System Status",
        border_style="blue",
    ))
    
    # Check if history exists
    history_file = os.path.join(config.data_dir, "history.json")
    if os.path.exists(history_file):
        size = os.path.getsize(history_file)
        console.print(f"\n[dim]Historical data file: {size/1024:.1f}KB[/dim]")
    else:
        console.print("\n[dim]No historical data yet (will be created on first run)[/dim]")


def main():
    """Main entry point."""
    args = sys.argv[1:]
    
    if not args or args[0] in ("-h", "--help", "help"):
        print_banner()
        console.print(
            "\n[bold]Usage:[/bold]\n"
            "  python cli.py [command]\n\n"
            "[bold]Commands:[/bold]\n"
            "  monitor    Fetch live bridge data from DeFiLlama\n"
            "  analyze    Run full anomaly and exploit analysis\n"
            "  report     Generate comprehensive bridge report\n"
            "  alerts     Check for suspicious activity alerts\n"
            "  chains     List all monitored chains\n"
            "  status     Show system status\n"
            "  help       Show this help message\n"
        )
        return
    
    verbose = "--verbose" in args or "-v" in args
    setup_logging(verbose)
    
    command = args[0].lower()
    
    print_banner()
    
    start = time.time()
    
    try:
        if command == "monitor":
            cmd_monitor()
        elif command == "analyze":
            cmd_analyze()
        elif command == "report":
            cmd_report()
        elif command == "alerts":
            cmd_alerts()
        elif command == "chains":
            cmd_chains()
        elif command == "status":
            cmd_status()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Run [bold]python cli.py help[/bold] for available commands.")
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red bold]Error: {e}[/red bold]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    elapsed = time.time() - start
    console.print(f"\n[dim]Completed in {elapsed:.1f}s[/dim]")


if __name__ == "__main__":
    main()
