#!/usr/bin/env python3
"""
Mirai CLI Setup Script
Makes the CLI tool easily accessible system-wide.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def setup_cli():
    """Setup Mirai CLI tool for system-wide access."""
    
    print("🚀 Setting up Mirai CLI...")
    
    # Get paths
    project_root = Path(__file__).parent
    cli_script = project_root / "mirai.py"
    
    # Check if CLI script exists
    if not cli_script.exists():
        print(f"❌ CLI script not found at {cli_script}")
        return False
    
    # Make script executable
    cli_script.chmod(0o755)
    
    # Try to create symlink in user's local bin
    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    
    symlink_path = local_bin / "mirai"
    
    # Remove existing symlink if it exists
    if symlink_path.exists():
        symlink_path.unlink()
    
    try:
        # Create symlink
        symlink_path.symlink_to(cli_script)
        print(f"✅ Created symlink: {symlink_path} -> {cli_script}")
        
        # Check if ~/.local/bin is in PATH
        path_env = os.environ.get('PATH', '')
        if str(local_bin) not in path_env:
            print(f"⚠️  Add {local_bin} to your PATH:")
            print(f"   echo 'export PATH=\"{local_bin}:$PATH\"' >> ~/.bashrc")
            print(f"   source ~/.bashrc")
        
        print("✅ Mirai CLI setup complete!")
        print("\nUsage:")
        print("  mirai --help")
        print("  mirai status health")
        print("  mirai trading trades")
        print("  mirai config set --api-url http://localhost:8001")
        
        return True
        
    except OSError as e:
        print(f"❌ Failed to create symlink: {e}")
        print(f"💡 Try running: ln -s {cli_script} {symlink_path}")
        return False

def install_dependencies():
    """Install CLI dependencies."""
    print("📦 Installing CLI dependencies...")
    
    dependencies = [
        "click>=8.0.0",
        "rich>=12.0.0",
        "requests>=2.25.0"
    ]
    
    try:
        for dep in dependencies:
            print(f"  Installing {dep}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try: pip install click rich requests")
        return False

def main():
    """Main setup function."""
    print("Mirai CLI Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Setup CLI
    if not setup_cli():
        return 1
    
    print("\n🎉 Setup complete! You can now use the 'mirai' command.")
    return 0

if __name__ == "__main__":
    sys.exit(main())