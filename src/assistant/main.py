import os
import sys
import platform
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
import json
from google import genai
import pyperclip
import questionary

# Setup Rich Console
console = Console()

# Pathing
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
MEMORY_FILE = ROOT_DIR / ".ada_memory.json"

DEFAULT_SYSTEM_PROMPT = (
    "You are ADA, an Automated Directive Assistant. The user is on {os} using {shell}. "
    "Your goal is to assist the user with terminal commands or general technical/topical queries. "
    "\n\nMODES:"
    "\n1. COMMAND MODE: If the user asks for a task that requires a terminal command, provide it."
    "\n2. CHAT MODE: If the user asks a general question, follow-up, or explanation that doesn't require a command, respond concisely."
    "\n\nCRITICAL (Command Mode): The command MUST be natively compatible with {shell}. "
    "\nSTYLE GUIDELINES:"
    "\n- ALWAYS prefer the SHORTEST possible command and use common ALIASES (e.g., 'gci' or 'ls' instead of 'Get-ChildItem')."
    "\n- If the shell is PowerShell, DO NOT use CMD-specific switches like '/s'."
    "\n- If you use an alias, briefly mention what it stands for in the explanation."
    "\n- Keep chat responses concise and suitable for a terminal environment."
    "\n{history_context}"
    "\n\nFORMATTING:"
    "\n- If in COMMAND MODE: Return ONLY the terminal command on Line 1. Return the explanation on Line 2+."
    "\n- If in CHAT MODE: Return 'NONE' on Line 1. Return your concise response on Line 2+."
)

def setup_env():
    """First-run wizard to set up API key if missing."""
    load_dotenv(ENV_FILE)
    api_key = os.getenv("GEMINI_ADA_API_KEY")

    if not api_key:
        title = pyfiglet.figlet_format("ADA", font="slant")
        console.print(Panel(Text(title, style="bold cyan"), subtitle="Automated Directive Assistant", expand=False))
        console.print("[bold green]Welcome to ADA![/bold green] Let's set up your Gemini API Key.")
        
        api_key = Prompt.ask("Enter your Gemini API Key")
        
        # Ensure .env exists in project root
        if not ENV_FILE.exists():
            ENV_FILE.touch()
        
        set_key(str(ENV_FILE), "GEMINI_ADA_API_KEY", api_key)
        console.print("[dim]Key saved to .env[/dim]\n")
        load_dotenv(ENV_FILE) # Reload to ensure it's in environment
        
    return os.getenv("GEMINI_ADA_API_KEY")

def detect_shell():
    """Detect the current shell environment."""
    parent_process = ""
    try:
        import psutil
        parent_process = psutil.Process(os.getppid()).name().lower()
    except ImportError:
        # Fallback if psutil isn't installed
        if os.name == 'nt':
            if os.getenv('PSModulePath'):
                parent_process = "powershell"
            else:
                parent_process = "cmd"
        else:
            parent_process = os.getenv('SHELL', 'bash').split('/')[-1]
    
    if "pwsh" in parent_process or "powershell" in parent_process:
        return "PowerShell"
    elif "cmd" in parent_process:
        return "Command Prompt (CMD)"
    elif "bash" in parent_process:
        return "Bash"
    elif "zsh" in parent_process:
        return "Zsh"
    return parent_process or "Terminal"

def get_system_prompt():
    """Get the current system prompt, preferring override from .env."""
    load_dotenv(ENV_FILE)
    return os.getenv("ADA_SYSTEM_PROMPT_OVERRIDE", DEFAULT_SYSTEM_PROMPT)

def set_system_prompt(prompt):
    """Set the system prompt override in .env."""
    if not prompt or prompt.strip() == "reset":
        unset_key(str(ENV_FILE), "ADA_SYSTEM_PROMPT_OVERRIDE")
        console.print("[bold green]System prompt reset to default.[/bold green]")
    else:
        set_key(str(ENV_FILE), "ADA_SYSTEM_PROMPT_OVERRIDE", prompt)
        console.print("[bold green]System prompt updated.[/bold green]")

def get_max_memory():
    """Get max memory from env, with a sensible limit of 20."""
    load_dotenv(ENV_FILE)
    try:
        limit = int(os.getenv("ADA_MEMORY_LIMIT", 5))
        return min(max(1, limit), 20)
    except:
        return 5

def set_max_memory(limit):
    """Update max memory limit in .env."""
    try:
        val = int(limit)
        if 1 <= val <= 20:
            set_key(str(ENV_FILE), "ADA_MEMORY_LIMIT", str(val))
            console.print(f"[bold green]Memory limit set to {val}.[/bold green]")
        else:
            console.print("[bold red]Limit must be between 1 and 20.[/bold red]")
    except ValueError:
        console.print("[bold red]Invalid limit value.[/bold red]")

def load_memory():
    """Load interaction history from disk."""
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(query, response):
    """Save the latest interaction and prune old ones based on limit."""
    memory = load_memory()
    memory.append({"query": query, "response": response})
    
    limit = get_max_memory()
    if len(memory) > limit:
        memory = memory[-limit:]
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def clear_memory():
    """Delete the memory file."""
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()
    console.print("[bold green]Memories cleared![/bold green]")

def show_memory():
    """Display stored interactions."""
    memory = load_memory()
    limit = get_max_memory()
    console.print(f"[dim]Memory Limit: {limit} interactions[/dim]")
    if not memory:
        console.print("[dim]No memories found.[/dim]")
        return
    
    for i, entry in enumerate(memory, 1):
        console.print(Panel(
            f"[bold cyan]Q:[/bold cyan] {entry['query']}\n[bold green]A:[/bold green] {entry['response'].splitlines()[0]}",
            title=f"Memory {i}",
            expand=False
        ))

def handle_management_command(args):
    """Process /memories and /prompt commands. Returns True if handled."""
    if not args: return False
    cmd = args[0].lower()
    
    if cmd.startswith("/mem"):
        subcmd = args[1].lower() if len(args) > 1 else "show"
        if subcmd == "clear":
            clear_memory()
        elif subcmd == "limit":
            if len(args) > 2:
                set_max_memory(args[2])
            else:
                console.print(f"[bold yellow]Current limit: {get_max_memory()}[/bold yellow]")
        else:
            show_memory()
        return True
    
    elif cmd.startswith("/prompt"):
        subcmd = args[1].lower() if len(args) > 1 else "show"
        if subcmd == "edit":
            new_prompt = Prompt.ask("Enter new system prompt (or 'reset' to use default)")
            set_system_prompt(new_prompt)
        else:
            console.print(Panel(get_system_prompt(), title="Current System Prompt", border_style="yellow"))
            console.print("[dim]Use 'ada /prompt edit' to modify.[/dim]")
        return True
        
    return False

def get_ada_response(query, api_key, memory):
    """Call Gemini API for the terminal command, with memory context."""
    client = genai.Client(api_key=api_key)
    current_os = platform.system()
    current_shell = detect_shell()
    
    # Build history context
    history_context = ""
    if memory:
        history_context = "\nRecent interactions for context:\n"
        for m in memory:
            history_context += f"User: {m['query']}\nADA: {m['response'].splitlines()[0]}\n"

    template = get_system_prompt()
    try:
        system_prompt = template.format(
            os=current_os,
            shell=current_shell,
            history_context=history_context
        )
    except KeyError as e:
        console.print(f"[bold red]System Prompt Error:[/bold red] Missing variable {e}")
        console.print("[dim]Resetting to default prompt...[/dim]")
        set_system_prompt("reset")
        return get_ada_response(query, api_key, memory)

    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview', 
            config={'system_instruction': system_prompt},
            contents=query
        )
        return response.text.strip()
    except Exception as e:
        console.print(f"[bold red]Error calling Gemini API:[/bold red] {e}")
        sys.exit(1)

def run_query(query, api_key):
    """Execute a query and handle the response."""
    memory = load_memory()
    with console.status("[bold blue]Thinking...[/bold blue]"):
        full_response = get_ada_response(query, api_key, memory)

    # Parse response
    lines = full_response.split('\n')
    header = lines[0].strip()
    explanation = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    if header.upper() == "NONE":
        console.print(f"\n[bold cyan]ADA:[/bold cyan] {explanation}\n")
        save_memory(query, full_response)
    else:
        command = header
        console.print("\n[bold white]Suggested Command:[/bold white]")
        console.print(Panel(Text(command, style="bold green"), border_style="cyan"))
        
        if command:
            try:
                pyperclip.copy(command)
                console.print("[dim]Command copied to clipboard![/dim]")
                save_memory(query, full_response)
            except Exception as e:
                console.print(f"[dim red]Failed to copy to clipboard: {e}[/dim red]")
        
        if explanation:
            console.print(f"[dim]{explanation}[/dim]\n")

def main():
    try:
        # Handle CLI management commands
        if len(sys.argv) > 1 and sys.argv[1].startswith("/"):
            if handle_management_command(sys.argv[1:]):
                return

        # Handle first-run/env setup
        api_key = setup_env()
        
        # Check for direct query via CLI args
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            run_query(query, api_key)
            return

        # Interactive Menu
        while True:
            console.clear()
            title_text = pyfiglet.figlet_format("ADA", font="slant")
            console.print(Text(title_text, style="bold cyan"))
            
            choice = questionary.select(
                "Main Menu",
                choices=[
                    "Ask a Question",
                    "Manage Memory",
                    "System Settings",
                    "Exit"
                ]
            ).ask()
            
            if choice == "Ask a Question":
                query = questionary.text("How can I help you?").ask()
                if query and query.strip():
                    run_query(query, api_key)
                    questionary.press_any_key_to_continue().ask()
            
            elif choice == "Manage Memory":
                mem_choice = questionary.select(
                    "Memory Management",
                    choices=[
                        "Show Memories",
                        "Clear Memories",
                        "Back"
                    ]
                ).ask()
                if mem_choice == "Show Memories": 
                    show_memory()
                    questionary.press_any_key_to_continue().ask()
                elif mem_choice == "Clear Memories": 
                    clear_memory()
                    questionary.press_any_key_to_continue().ask()
                
            elif choice == "System Settings":
                sys_choice = questionary.select(
                    "System Settings",
                    choices=[
                        "Show System Prompt",
                        "Edit System Prompt",
                        "Set Memory Limit",
                        "Back"
                    ]
                ).ask()
                if sys_choice == "Show System Prompt": 
                    handle_management_command(["/prompt", "show"])
                    questionary.press_any_key_to_continue().ask()
                elif sys_choice == "Edit System Prompt": 
                    handle_management_command(["/prompt", "edit"])
                    questionary.press_any_key_to_continue().ask()
                elif sys_choice == "Set Memory Limit": 
                    limit = questionary.text("Enter memory limit (1-20)").ask()
                    if limit:
                        set_max_memory(limit)
                        questionary.press_any_key_to_continue().ask()
                
            elif choice == "Exit" or choice is None:
                console.print("[dim]Goodbye![/dim]")
                break
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")
        sys.exit(0)

if __name__ == "__main__":
    main()
