#!/usr/bin/env python3
"""
QR Configuration Management
Handle user preferences and configuration files
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    "qr_settings": {
        "box_size": 10,
        "border": 4,
        "error_correction": "L",
        "max_chunk_size": 2362  # Conservative estimate
    },
    "sheet_settings": {
        "enabled": True,
        "size": 9,
        "columns": 3,
        "padding": 20
    },
    "output_settings": {
        "display": "none",
        "cleanup": False,
        "force": False,
        "verbose": False,
        "quiet": False
    },
    "scanning_settings": {
        "verify_checksums": True,
        "auto_reconstruct": False,
        "output_dir": "./scanned_chunks"
    },
    "security_settings": {
        "enable_checksums": True,
        "hash_algorithm": "sha256"
    }
}

class QRConfig:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path"""
        if sys.platform.startswith('win'):
            # Windows: Use AppData
            config_dir = os.path.expanduser("~\\AppData\\Local\\QR-Transfer")
        elif sys.platform.startswith('darwin'):
            # macOS: Use ~/Library/Application Support
            config_dir = os.path.expanduser("~/Library/Application Support/QR-Transfer")
        else:
            # Linux: Use XDG config directory
            config_dir = os.path.expanduser("~/.config/qr-transfer")
        
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        if not os.path.exists(self.config_path):
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            # Merge saved config with defaults (preserves new defaults for missing keys)
            self._merge_config(self.config, saved_config)
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            
            return True
            
        except IOError as e:
            print(f"Error: Could not save config to {self.config_path}: {e}")
            return False
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section"""
        return self.config.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """Set an entire configuration section"""
        self.config[section] = values
    
    def update_from_args(self, args) -> None:
        """Update configuration from command line arguments"""
        # QR settings - only update if explicitly provided and not None
        if hasattr(args, 'box_size') and args.box_size is not None:
            self.set('qr_settings', 'box_size', args.box_size)
        
        if hasattr(args, 'border') and args.border is not None:
            self.set('qr_settings', 'border', args.border)
        
        # Sheet settings
        if hasattr(args, 'sheet') and args.sheet:
            self.set('sheet_settings', 'enabled', args.sheet)
        
        if hasattr(args, 'sheet_size') and args.sheet_size is not None:
            self.set('sheet_settings', 'size', args.sheet_size)
        
        if hasattr(args, 'sheet_cols') and args.sheet_cols is not None:
            self.set('sheet_settings', 'columns', args.sheet_cols)
        
        # Output settings
        if hasattr(args, 'display') and args.display is not None:
            self.set('output_settings', 'display', args.display)
        
        if hasattr(args, 'cleanup') and args.cleanup:
            self.set('output_settings', 'cleanup', args.cleanup)
        
        if hasattr(args, 'force') and args.force:
            self.set('output_settings', 'force', args.force)
        
        if hasattr(args, 'verbose') and args.verbose:
            self.set('output_settings', 'verbose', args.verbose)
        
        if hasattr(args, 'quiet') and args.quiet:
            self.set('output_settings', 'quiet', args.quiet)
        
        # Scanning settings
        if hasattr(args, 'output') and args.output is not None and args.output != DEFAULT_CONFIG['scanning_settings']['output_dir']:
            self.set('scanning_settings', 'output_dir', args.output)
        
        if hasattr(args, 'auto_reconstruct') and args.auto_reconstruct:
            self.set('scanning_settings', 'auto_reconstruct', args.auto_reconstruct)
    
    def apply_to_args(self, args) -> None:
        """Apply configuration to command line arguments (fill in defaults)"""
        # Only apply if not explicitly set by user and ensure we don't set None values
        if getattr(args, 'box_size', None) is None:
            config_value = self.get('qr_settings', 'box_size', DEFAULT_CONFIG['qr_settings']['box_size'])
            args.box_size = config_value if config_value is not None else DEFAULT_CONFIG['qr_settings']['box_size']
        
        if getattr(args, 'border', None) is None:
            config_value = self.get('qr_settings', 'border', DEFAULT_CONFIG['qr_settings']['border'])
            args.border = config_value if config_value is not None else DEFAULT_CONFIG['qr_settings']['border']
        
        if not getattr(args, 'sheet', False):
            config_value = self.get('sheet_settings', 'enabled', DEFAULT_CONFIG['sheet_settings']['enabled'])
            args.sheet = config_value if config_value is not None else DEFAULT_CONFIG['sheet_settings']['enabled']
        
        if getattr(args, 'sheet_size', None) is None:
            config_value = self.get('sheet_settings', 'size', DEFAULT_CONFIG['sheet_settings']['size'])
            args.sheet_size = config_value if config_value is not None else DEFAULT_CONFIG['sheet_settings']['size']
        
        if getattr(args, 'sheet_cols', None) is None:
            config_value = self.get('sheet_settings', 'columns', DEFAULT_CONFIG['sheet_settings']['columns'])
            args.sheet_cols = config_value if config_value is not None else DEFAULT_CONFIG['sheet_settings']['columns']
        
        if getattr(args, 'display', None) is None:
            config_value = self.get('output_settings', 'display', DEFAULT_CONFIG['output_settings']['display'])
            args.display = config_value if config_value is not None else DEFAULT_CONFIG['output_settings']['display']
        
        if not getattr(args, 'cleanup', False):
            config_value = self.get('output_settings', 'cleanup', DEFAULT_CONFIG['output_settings']['cleanup'])
            args.cleanup = config_value if config_value is not None else DEFAULT_CONFIG['output_settings']['cleanup']
        
        if not getattr(args, 'force', False):
            config_value = self.get('output_settings', 'force', DEFAULT_CONFIG['output_settings']['force'])
            args.force = config_value if config_value is not None else DEFAULT_CONFIG['output_settings']['force']
        
        if not getattr(args, 'verbose', False):
            config_value = self.get('output_settings', 'verbose', DEFAULT_CONFIG['output_settings']['verbose'])
            args.verbose = config_value if config_value is not None else DEFAULT_CONFIG['output_settings']['verbose']
        
        if not getattr(args, 'quiet', False):
            config_value = self.get('output_settings', 'quiet', DEFAULT_CONFIG['output_settings']['quiet'])
            args.quiet = config_value if config_value is not None else DEFAULT_CONFIG['output_settings']['quiet']
    
    def print_config(self) -> None:
        """Print current configuration"""
        print("📋 Current Configuration:")
        print(f"  Config file: {self.config_path}")
        print()
        
        for section, values in self.config.items():
            print(f"[{section}]")
            for key, value in values.items():
                print(f"  {key} = {value}")
            print()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = DEFAULT_CONFIG.copy()
    
    def create_sample_config(self, path: Optional[str] = None) -> str:
        """Create a sample configuration file"""
        sample_path = path or "qr-config-sample.json"
        
        sample_config = DEFAULT_CONFIG.copy()
        sample_config["_comment"] = {
            "description": "QR File Transfer Tool Configuration",
            "generated": "This is a sample configuration file",
            "usage": "Copy to ~/.config/qr-transfer/config.json and modify as needed"
        }
        
        try:
            with open(sample_path, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2)
            
            return sample_path
            
        except IOError as e:
            print(f"Error creating sample config: {e}")
            return ""

def main():
    """Configuration tool main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="QR Transfer Configuration Tool")
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--reset', action='store_true', help='Reset to default configuration')
    parser.add_argument('--sample', action='store_true', help='Create sample configuration file')
    parser.add_argument('--config', help='Specify configuration file path')
    
    args = parser.parse_args()
    
    config = QRConfig(args.config)
    
    if args.show:
        config.print_config()
    elif args.reset:
        config.reset_to_defaults()
        if config.save_config():
            print("✅ Configuration reset to defaults")
        else:
            print("❌ Failed to save configuration")
    elif args.sample:
        sample_path = config.create_sample_config()
        if sample_path:
            print(f"✅ Sample configuration created: {sample_path}")
    else:
        config.print_config()

if __name__ == "__main__":
    main() 