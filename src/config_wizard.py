"""
Configuration wizard for meshtrbl initial setup.
Implements Phase 4.1 configuration wizard feature.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

try:
    import questionary
    from questionary import Style
    QUESTIONARY_AVAILABLE = True
    # Custom style for questionary
    custom_style = Style([
        ('qmark', 'fg:#673ab7 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#2196f3 bold'),
        ('pointer', 'fg:#673ab7 bold'),
        ('highlighted', 'fg:#673ab7 bold'),
        ('selected', 'fg:#4caf50'),
        ('separator', 'fg:#cc5454'),
        ('instruction', ''),
        ('text', ''),
    ])
except ImportError:
    QUESTIONARY_AVAILABLE = False
    custom_style = None

from .ux_utils import console, print_header, print_success, print_error, print_warning, print_info


class ConfigWizard:
    """Interactive configuration wizard for meshtrbl."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".meshtrbl"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
    
    @staticmethod
    def get_kubernetes_contexts() -> list[str]:
        """Get available Kubernetes contexts."""
        try:
            from kubernetes import config
            contexts, _ = config.list_kube_config_contexts()
            return [ctx['name'] for ctx in contexts]
        except Exception:
            return []
    
    @staticmethod
    def get_kubernetes_namespaces(context: Optional[str] = None) -> list[str]:
        """Get available Kubernetes namespaces."""
        try:
            from kubernetes import client, config
            if context:
                config.load_kube_config(context=context)
            else:
                config.load_kube_config()
            v1 = client.CoreV1Api()
            namespaces = v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except Exception:
            return ["default", "kube-system"]
    
    @staticmethod
    def validate_openai_key(api_key: str) -> bool:
        """Validate OpenAI API key."""
        if not api_key or len(api_key) < 20:
            return False
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            client.models.list()
            return True
        except Exception:
            return False
    
    @staticmethod
    def run_wizard() -> Dict[str, Any]:
        """Run the interactive configuration wizard."""
        if not QUESTIONARY_AVAILABLE:
            print_error("Configuration wizard requires 'questionary' package.")
            console.print("[yellow]Install it with: pip install questionary[/yellow]")
            console.print("[dim]Or manually create ~/.meshtrbl/config.yaml[/dim]")
            sys.exit(1)
        
        print_header("meshtrbl Configuration Wizard", "Let's set up your troubleshooting agent! 🚀")
        
        console.print("\n[dim]This wizard will help you configure meshtrbl for your environment.[/dim]")
        console.print("[dim]You can change these settings later by editing ~/.meshtrbl/config.yaml[/dim]\n")
        
        config = {}
        
        # OpenAI API Key
        console.print("[bold cyan]1. OpenAI Configuration[/bold cyan]")
        existing_key = os.getenv("OPENAI_API_KEY")
        
        if existing_key:
            use_existing = questionary.confirm(
                f"Found OPENAI_API_KEY in environment. Use it?",
                default=True,
                style=custom_style
            ).ask()
            
            if use_existing:
                config['openai_api_key'] = existing_key
                print_success("Using existing OpenAI API key from environment")
            else:
                api_key = questionary.password(
                    "Enter your OpenAI API key:",
                    style=custom_style
                ).ask()
                
                if api_key:
                    console.print("[dim]Validating API key...[/dim]")
                    if ConfigWizard.validate_openai_key(api_key):
                        config['openai_api_key'] = api_key
                        print_success("API key validated successfully!")
                    else:
                        print_warning("Could not validate API key. Saving anyway.")
                        config['openai_api_key'] = api_key
        else:
            api_key = questionary.password(
                "Enter your OpenAI API key:",
                style=custom_style
            ).ask()
            
            if api_key:
                console.print("[dim]Validating API key...[/dim]")
                if ConfigWizard.validate_openai_key(api_key):
                    config['openai_api_key'] = api_key
                    print_success("API key validated successfully!")
                else:
                    print_warning("Could not validate API key. Saving anyway.")
                    config['openai_api_key'] = api_key
            else:
                print_error("OpenAI API key is required!")
                sys.exit(1)
        
        # Model selection
        model = questionary.select(
            "Select OpenAI model:",
            choices=[
                "gpt-4o-mini (Recommended - Fast & Cost-effective)",
                "gpt-4o (More capable, higher cost)",
                "gpt-4-turbo (Previous generation)",
            ],
            style=custom_style
        ).ask()
        
        config['model'] = model.split()[0]  # Extract model name
        
        # Kubernetes Configuration
        console.print("\n[bold cyan]2. Kubernetes Configuration[/bold cyan]")
        
        contexts = ConfigWizard.get_kubernetes_contexts()
        if contexts:
            context = questionary.select(
                "Select Kubernetes context:",
                choices=contexts + ["Enter manually"],
                style=custom_style
            ).ask()
            
            if context != "Enter manually":
                config['kubernetes_context'] = context
                
                # Get namespaces for selected context
                namespaces = ConfigWizard.get_kubernetes_namespaces(context)
                if namespaces:
                    namespace = questionary.select(
                        "Select default namespace:",
                        choices=namespaces + ["Enter manually"],
                        style=custom_style
                    ).ask()
                    
                    if namespace != "Enter manually":
                        config['kubernetes_namespace'] = namespace
                    else:
                        namespace = questionary.text(
                            "Enter namespace:",
                            default="default",
                            style=custom_style
                        ).ask()
                        config['kubernetes_namespace'] = namespace
                else:
                    namespace = questionary.text(
                        "Enter default namespace:",
                        default="default",
                        style=custom_style
                    ).ask()
                    config['kubernetes_namespace'] = namespace
            else:
                namespace = questionary.text(
                    "Enter default namespace:",
                    default="default",
                    style=custom_style
                ).ask()
                config['kubernetes_namespace'] = namespace
        else:
            print_warning("No Kubernetes contexts found. Using defaults.")
            namespace = questionary.text(
                "Enter default namespace:",
                default="default",
                style=custom_style
            ).ask()
            config['kubernetes_namespace'] = namespace
        
        # Consul Configuration
        console.print("\n[bold cyan]3. Consul Configuration[/bold cyan]")
        
        consul_host = questionary.text(
            "Consul server host:",
            default="localhost",
            style=custom_style
        ).ask()
        config['consul_host'] = consul_host
        
        consul_port = questionary.text(
            "Consul server port:",
            default="8500",
            style=custom_style
        ).ask()
        config['consul_port'] = int(consul_port)
        
        use_consul_token = questionary.confirm(
            "Do you use Consul ACL tokens?",
            default=False,
            style=custom_style
        ).ask()
        
        if use_consul_token:
            consul_token = questionary.password(
                "Enter Consul ACL token:",
                style=custom_style
            ).ask()
            if consul_token:
                config['consul_token'] = consul_token
        
        # Feature Configuration
        console.print("\n[bold cyan]4. Feature Configuration[/bold cyan]")
        
        config['enable_memory'] = questionary.confirm(
            "Enable conversation memory? (Remembers context across queries)",
            default=True,
            style=custom_style
        ).ask()
        
        config['enable_cache'] = questionary.confirm(
            "Enable session caching? (Faster repeated queries)",
            default=True,
            style=custom_style
        ).ask()
        
        config['enable_intent_routing'] = questionary.confirm(
            "Enable intent routing? (Fast-path for common issues)",
            default=True,
            style=custom_style
        ).ask()
        
        config['enable_workflow'] = questionary.confirm(
            "Enable LangGraph workflows? (Advanced troubleshooting)",
            default=True,
            style=custom_style
        ).ask()
        
        # Advanced Settings
        console.print("\n[bold cyan]5. Advanced Settings[/bold cyan]")
        
        configure_advanced = questionary.confirm(
            "Configure advanced settings? (cache TTL, max iterations, etc.)",
            default=False,
            style=custom_style
        ).ask()
        
        if configure_advanced:
            cache_ttl = questionary.text(
                "Cache TTL in seconds:",
                default="300",
                style=custom_style
            ).ask()
            config['cache_ttl'] = int(cache_ttl)
            
            max_iterations = questionary.text(
                "Maximum tool calls per query:",
                default="35",
                style=custom_style
            ).ask()
            config['max_iterations'] = int(max_iterations)
            
            max_time = questionary.text(
                "Maximum execution time in seconds:",
                default="300",
                style=custom_style
            ).ask()
            config['max_execution_time'] = int(max_time)
        else:
            # Use defaults
            config['cache_ttl'] = 300
            config['max_iterations'] = 35
            config['max_execution_time'] = 300
        
        return config
    
    @staticmethod
    def save_config(config: Dict[str, Any], config_file: Optional[Path] = None) -> bool:
        """Save configuration to file."""
        if config_file is None:
            config_file = ConfigWizard.DEFAULT_CONFIG_FILE
        
        try:
            # Create config directory if it doesn't exist
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            return True
        except Exception as e:
            print_error(f"Failed to save configuration: {e}")
            return False
    
    @staticmethod
    def load_config(config_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        if config_file is None:
            config_file = ConfigWizard.DEFAULT_CONFIG_FILE
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return None
    
    @staticmethod
    def run_setup():
        """Run the complete setup wizard."""
        print_header("Welcome to meshtrbl! 🚀", "AI-powered Kubernetes & Consul troubleshooting")
        
        # Check if config already exists
        if ConfigWizard.DEFAULT_CONFIG_FILE.exists():
            console.print(f"\n[yellow]Configuration file already exists:[/yellow] {ConfigWizard.DEFAULT_CONFIG_FILE}")
            
            if QUESTIONARY_AVAILABLE:
                overwrite = questionary.confirm(
                    "Do you want to overwrite it?",
                    default=False,
                    style=custom_style
                ).ask()
                
                if not overwrite:
                    console.print("\n[green]Setup cancelled. Using existing configuration.[/green]")
                    return
            else:
                console.print("[yellow]Run with --force to overwrite[/yellow]")
                return
        
        # Run wizard
        config = ConfigWizard.run_wizard()
        
        # Save configuration
        console.print("\n[cyan]Saving configuration...[/cyan]")
        if ConfigWizard.save_config(config):
            print_success(f"Configuration saved to {ConfigWizard.DEFAULT_CONFIG_FILE}")
            
            console.print("\n[bold green]✓ Setup complete![/bold green]")
            console.print("\n[dim]You can now run:[/dim]")
            console.print("  [cyan]meshtrbl[/cyan]                    # Start interactive chat")
            console.print("  [cyan]meshtrbl --query \"...\"[/cyan]      # Single query mode")
            console.print("\n[dim]To reconfigure, run:[/dim]")
            console.print("  [cyan]meshtrbl --setup[/cyan]")
        else:
            print_error("Failed to save configuration!")
            sys.exit(1)


def main():
    """Run the configuration wizard."""
    ConfigWizard.run_setup()


if __name__ == "__main__":
    main()

# Made with Bob
