"""
Interactive CLI for the marketplace analyzer with CrewAI integration.
A production-grade Pakistani e-commerce price intelligence system.
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from src.crew.crew import run_clean_marketplace_analysis

# Load environment variables
load_dotenv()

console = Console()


def display_banner():
    """Display the application banner."""
    banner = """
    🛒 Pakistani E-commerce Marketplace Analyzer
    ════════════════════════════════════════════
    
    🚀 Powered by CLEAN CrewAI Architecture
    📊 Optimized 3-Agent Price Intelligence System
    🔍 Scrapes: Daraz.pk, PriceOye, Telemart & More
    💡 Works for ALL Products: Electronics, Fashion, Home, Books
    ⚡ Agent B: Direct Processing (NO Agent C needed)
    
    ════════════════════════════════════════════
    """
    console.print(Panel(banner, border_style="bright_blue", padding=(1, 2)))


def get_user_preferences():
    """Get user preferences interactively."""
    console.print("\n[bold cyan]🔧 Configure Your Search Settings[/bold cyan]")
    
    # Product query with diverse examples
    examples = ["Laptop Dell", "Nike Air Max", "Office Chair", "iPhone 15", "Samsung Galaxy", "Gaming Mouse", "Instant Pot"]
    default_query = examples[0]  # Use first example as default
    
    console.print(f"[dim]Examples: {', '.join(examples)}[/dim]")
    query = Prompt.ask(
        "[yellow]🔍 Enter product name to search for[/yellow]",
        default=default_query
    ).strip()
    
    # Max results
    max_results = Prompt.ask(
        "[yellow]📊 Maximum results per marketplace[/yellow]",
        default="3",
        show_default=True
    )
    try:
        max_results = int(max_results)
    except ValueError:
        max_results = 3
    
    # Browser mode
    headless = not Confirm.ask(
        "[yellow]🖥️  Show browser window while scraping?[/yellow]",
        default=True
    )
    
    # Timeout
    timeout_seconds = Prompt.ask(
        "[yellow]⏱️  Timeout per page (seconds)[/yellow]",
        default="30",
        show_default=True
    )
    try:
        timeout = int(timeout_seconds) * 1000  # Convert to milliseconds
    except ValueError:
        timeout = 30000
    
    # Advanced options
    advanced = Confirm.ask(
        "[yellow]🔧 Configure advanced options?[/yellow]",
        default=False
    )
    
    index = 0
    
    if advanced:
        index_input = Prompt.ask(
            "[yellow]🎯 Daraz result index to select[/yellow]",
            default="0",
            show_default=True
        )
        try:
            index = int(index_input)
        except ValueError:
            index = 0
    
    return {
        'query': query,
        'max_results': max_results,
        'headless': headless,
        'timeout': timeout,
        'index': index
    }


def display_progress_info(stage: str, details: str = ""):
    """Display current processing stage."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"[dim]{timestamp}[/dim] [bold green]●[/bold green] {stage}", end="")
    if details:
        console.print(f" [dim]({details})[/dim]")
    else:
        console.print()


async def run_analysis_with_progress(config: dict):
    """Run the analysis with real-time progress updates."""
    console.print(f"\n[bold cyan]🔍 Starting CrewAI Analysis: '{config['query']}'[/bold cyan]")
    console.print("─" * 50)
    
    start_time = time.time()
    
    # Create progress tracker
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        
        # Add main task
        main_task = progress.add_task(
            f"Analyzing '{config['query']}'...", 
            total=None
        )
        
        try:
            # Run the CLEAN CrewAI analysis
            result = await run_clean_marketplace_analysis(
                query=config['query'],
                index=config['index'],
                headless=config['headless'],
                timeout=config['timeout'],
                max_results=config['max_results']
            )
            
            progress.update(main_task, description="✅ Analysis completed!")
            
        except Exception as e:
            progress.update(main_task, description=f"❌ Error: {str(e)}")
            result = {'status': 'failed', 'error': str(e)}
    
    elapsed_time = time.time() - start_time
    console.print(f"⏱️  [dim]Analysis completed in {elapsed_time:.2f}s[/dim]")
    
    return result


def display_results(result: dict):
    """Display analysis results in a formatted way."""
    if not result or result.get('status') != 'completed':
        console.print("[bold red]❌ Analysis was not completed successfully[/bold red]")
        if result and result.get('error'):
            console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    console.print("\n[bold green]📊 CREWAI ANALYSIS RESULTS[/bold green]")
    console.print("=" * 60)
    
    # Summary stats
    stats_table = Table(title="Summary Statistics", show_header=True, header_style="bold magenta")
    stats_table.add_column("Metric", style="cyan", no_wrap=True)
    stats_table.add_column("Value", style="green")
    
    results_data = result.get('results', {})
    
    stats_table.add_row("Query ID", str(result.get('query_id', 'N/A')))
    stats_table.add_row("Status", f"✅ {result.get('status', 'Unknown')}")
    stats_table.add_row("Products Found", str(results_data.get('total_products_found', 0)))
    stats_table.add_row("Execution Time", result.get('execution_time', 'N/A'))
    
    console.print(stats_table)
    
    # Show cheapest options
    cheapest_options = results_data.get('cheapest_options', [])
    if cheapest_options:
        console.print("\n[bold cyan]💰 PRICE COMPARISON[/bold cyan]")
        cheapest_table = Table(show_header=True, header_style="bold magenta")
        cheapest_table.add_column("Rank", style="cyan", width=6)
        cheapest_table.add_column("Platform", style="green")
        cheapest_table.add_column("Price", style="yellow")
        cheapest_table.add_column("Delta", style="blue")
        
        for i, option in enumerate(cheapest_options[:5], 1):
            platform = option.get('platform', 'Unknown')
            price = option.get('price', 'N/A')
            delta = option.get('delta_from_cheapest', 'N/A')
            
            cheapest_table.add_row(
                str(i),
                platform,
                price,
                delta
            )
        
        console.print(cheapest_table)
    
    # Show reports generated
    reports = results_data.get('reports_generated', [])
    if reports:
        console.print(f"\n[bold cyan]📄 REPORTS GENERATED[/bold cyan]")
        for report in reports:
            report_type = report.get('type', 'Unknown')
            report_path = report.get('path', 'N/A')
            console.print(f"• {report_type.title()}: [cyan]{report_path}[/cyan]")
            
            # Show preview
            preview = report.get('content_preview', '')
            if preview:
                console.print(f"  [dim]{preview}[/dim]")
    
    console.print(f"\n[dim]💾 All data saved to database: {result.get('database_path', 'N/A')}[/dim]")


def display_help():
    """Display help information."""
    help_text = """
    [bold cyan]🆘 How to Use This CrewAI Tool[/bold cyan]
    
    This tool uses CrewAI multi-agent system to analyze Pakistani e-commerce marketplaces:
    
    [yellow]🤖 What it does:[/yellow]
    • Agent A: Scrapes Daraz.pk with Playwright
    • Agent B: Searches other marketplaces with Groq AI 
    • Agent C: Analyzes pricing across platforms
    • Agent D: Generates detailed comparison reports
    • Works for ANY product category - electronics, fashion, home, books, etc.
    
    [yellow]🔍 Search Tips:[/yellow]
    • Electronics: "Dell Laptop i7", "iPhone 15 Pro 128GB", "Sony Headphones"
    • Fashion: "Nike Air Max 42", "Levi Jeans 32", "Formal Shirt XL"
    • Home: "Office Chair Ergonomic", "LED TV 55 inch", "Coffee Maker"
    • Books: "Python Programming", "Harry Potter", "Business Strategy"
    • Be specific with models, sizes, and brands for better results
    
    [yellow]⚡ Performance Tips:[/yellow]
    • Use headless mode for faster scraping
    • Set appropriate timeout for slow connections
    • Limit max results for quicker analysis
    
    [yellow]🤖 CrewAI Features:[/yellow]
    • Sequential task execution with proper dependencies
    • Groq AI rate limiting with exponential backoff
    • Comprehensive error handling and logging
    • Structured data output with database storage
    """
    console.print(Panel(help_text, border_style="yellow", padding=(1, 2)))


async def interactive_main():
    """Interactive main function."""
    display_banner()
    
    while True:
        console.print("\n[bold cyan]🏠 Main Menu[/bold cyan]")
        console.print("1. 🔍 Start New CrewAI Analysis")
        console.print("2. 🆘 Help & Tips")
        console.print("3. 🚪 Exit")
        
        choice = Prompt.ask(
            "[yellow]Select an option[/yellow]",
            choices=["1", "2", "3"],
            default="1"
        )
        
        if choice == "1":
            # Get user preferences
            config = get_user_preferences()
            
            # Run analysis
            result = await run_analysis_with_progress(config)
            
            # Display results
            display_results(result)
        
        elif choice == "2":
            display_help()
        
        elif choice == "3":
            console.print("\n[bold green]👋 Thanks for using the CrewAI Marketplace Analyzer![/bold green]")
            break


async def cli_main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pakistani E-commerce Marketplace Analyzer with CrewAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "iPhone 15"
  python main.py "Portable SSD 500GB" --max-results 5 --headful
  python main.py "Gaming Laptop" --timeout 60000 --index 1
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Product search query (e.g., 'iPhone 15', 'Portable SSD 500GB')"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=3,
        help="Maximum results per marketplace (default: 3)"
    )
    
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Daraz result index to select (default: 0)"
    )
    
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser in headful mode for debugging"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Browser timeout in milliseconds (default: 30000)"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.interactive or not args.query:
        await interactive_main()
        return
    
    console.print("🚀 Pakistani E-commerce CrewAI Marketplace Analyzer")
    console.print("=" * 50)
    console.print(f"Query: {args.query}")
    console.print(f"Max Results: {args.max_results}")
    console.print(f"Browser Mode: {'Headful' if args.headful else 'Headless'}")
    console.print("=" * 50)
    
    try:
        # Run analysis
        config = {
            'query': args.query,
            'max_results': args.max_results,
            'index': args.index,
            'headless': not args.headful,
            'timeout': args.timeout
        }
        
        result = await run_analysis_with_progress(config)
        display_results(result)
        
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Analysis interrupted by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(cli_main())
    except KeyboardInterrupt:
        console.print("\n[bold red]❌ Interrupted by user[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Fatal error: {e}[/bold red]")
        sys.exit(1)
