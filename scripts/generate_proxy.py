#!/usr/bin/env python3
"""
Cropwise Unified Platform - Proxy Bundle Generator

This script generates an Apigee X proxy bundle with environment-specific
configurations for the cropwise-unified-platform proxy.

Usage:
    python scripts/generate_proxy.py --env dev
    python scripts/generate_proxy.py --env qa --output ./dist
    python scripts/generate_proxy.py --env prod --validate
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ProxyGenerator:
    """Generates Apigee X proxy bundles with environment-specific configurations."""
    
    def __init__(self, base_dir: str, env: str, config_path: str = None):
        self.base_dir = Path(base_dir)
        self.env = env
        self.config_path = config_path or self.base_dir / "config" / "environments.json"
        self.apiproxy_dir = self.base_dir / "apiproxy"
        self.config = self._load_config()
        self.env_config = self.config["environments"].get(env)
        
        if not self.env_config:
            raise ValueError(f"Environment '{env}' not found in configuration")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load environment configuration from JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _update_target_endpoint(self, target_file: Path, temp_dir: Path) -> None:
        """Update target endpoint with environment-specific backend settings."""
        tree = ET.parse(target_file)
        root = tree.getroot()
        
        # Update HTTPTargetConnection
        http_target = root.find('.//HTTPTargetConnection')
        if http_target is not None:
            # Update URL
            url_elem = http_target.find('URL')
            if url_elem is not None:
                protocol = self.env_config.get('backend_protocol', 'https')
                host = self.env_config['backend_host']
                port = self.env_config.get('backend_port', 443)
                url_elem.text = f"{protocol}://{host}:{port}"
            
            # Update SSLInfo if exists
            ssl_info = http_target.find('SSLInfo')
            if ssl_info is None and self.env_config.get('backend_protocol') == 'https':
                ssl_info = ET.SubElement(http_target, 'SSLInfo')
                enabled = ET.SubElement(ssl_info, 'Enabled')
                enabled.text = 'true'
        
        # Write updated file
        output_file = temp_dir / "targets" / target_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _update_proxy_endpoint(self, proxy_file: Path, temp_dir: Path) -> None:
        """Update proxy endpoint with environment-specific settings."""
        tree = ET.parse(proxy_file)
        root = tree.getroot()
        
        # Update VirtualHosts
        http_proxy = root.find('.//HTTPProxyConnection')
        if http_proxy is not None:
            # Remove existing VirtualHost elements
            for vh in http_proxy.findall('VirtualHost'):
                http_proxy.remove(vh)
            
            # Add environment-specific VirtualHosts
            for vh_name in self.env_config.get('virtual_hosts', ['default', 'secure']):
                vh_elem = ET.SubElement(http_proxy, 'VirtualHost')
                vh_elem.text = vh_name
            
            # Update BasePath if specified
            base_path = http_proxy.find('BasePath')
            if base_path is not None and self.env_config.get('base_path'):
                base_path.text = self.env_config['base_path']
        
        # Write updated file
        output_file = temp_dir / "proxies" / proxy_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _update_logging_policy(self, policy_file: Path, temp_dir: Path) -> None:
        """Update logging policy with environment-specific syslog settings."""
        tree = ET.parse(policy_file)
        root = tree.getroot()
        
        # Update Syslog settings
        syslog = root.find('.//Syslog')
        if syslog is not None:
            host = syslog.find('Host')
            if host is not None:
                host.text = self.env_config.get('syslog_host', 'localhost')
            
            port = syslog.find('Port')
            if port is not None:
                port.text = str(self.env_config.get('syslog_port', 514))
        
        # Write updated file
        output_file = temp_dir / "policies" / policy_file.name
        output_file.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    def _copy_and_update_policies(self, temp_dir: Path) -> None:
        """Copy and update all policy files."""
        policies_dir = self.apiproxy_dir / "policies"
        output_policies_dir = temp_dir / "policies"
        output_policies_dir.mkdir(parents=True, exist_ok=True)
        
        for policy_file in policies_dir.glob("*.xml"):
            if policy_file.name == "FC-Syng-Logging.xml":
                self._update_logging_policy(policy_file, temp_dir)
            else:
                shutil.copy2(policy_file, output_policies_dir / policy_file.name)
    
    def _copy_resources(self, temp_dir: Path) -> None:
        """Copy JavaScript and other resource files."""
        resources_dir = self.apiproxy_dir / "resources"
        if resources_dir.exists():
            output_resources_dir = temp_dir / "resources"
            shutil.copytree(resources_dir, output_resources_dir)
    
    def _copy_proxy_descriptor(self, temp_dir: Path) -> None:
        """Copy and update the main proxy descriptor XML."""
        for xml_file in self.apiproxy_dir.glob("*.xml"):
            if xml_file.is_file():
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Update revision if needed
                revision = root.get('revision')
                if revision:
                    # Increment revision for new deployment
                    root.set('revision', str(int(revision) + 1))
                
                # Add deployment timestamp as description
                desc = root.find('Description')
                if desc is not None:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    desc.text = f"{desc.text} | Deployed: {timestamp} | Env: {self.env}"
                
                tree.write(temp_dir / xml_file.name, encoding='UTF-8', xml_declaration=True)
    
    def validate(self) -> bool:
        """Validate the proxy structure and configuration."""
        errors = []
        
        # Check required directories
        required_dirs = ['policies', 'proxies', 'targets']
        for dir_name in required_dirs:
            dir_path = self.apiproxy_dir / dir_name
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_name}")
        
        # Check required policies
        required_policies = [
            'AM-SetTarget.xml',
            'FC-Syng-Preflow.xml',
            'FC-Syng-ErrorHandling.xml',
            'FC-Syng-Logging.xml',
            'RF-APINotFound.xml'
        ]
        policies_dir = self.apiproxy_dir / "policies"
        for policy in required_policies:
            if not (policies_dir / policy).exists():
                errors.append(f"Missing required policy: {policy}")
        
        # Validate XML syntax
        for xml_file in self.apiproxy_dir.rglob("*.xml"):
            try:
                ET.parse(xml_file)
            except ET.ParseError as e:
                errors.append(f"Invalid XML in {xml_file.name}: {e}")
        
        if errors:
            print("Validation Errors:")
            for error in errors:
                print(f"  ❌ {error}")
            return False
        
        print("✅ Validation passed!")
        return True
    
    def generate(self, output_dir: str = None) -> str:
        """Generate the proxy bundle ZIP file."""
        output_path = Path(output_dir) if output_dir else self.base_dir / "dist"
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        bundle_name = f"cropwise-unified-platform-{self.env}-{timestamp}"
        temp_dir = output_path / bundle_name / "apiproxy"
        
        try:
            # Create temp directory structure
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Process all components
            print(f"Generating proxy bundle for environment: {self.env}")
            
            # Copy and update proxy descriptor
            print("  → Processing proxy descriptor...")
            self._copy_proxy_descriptor(temp_dir)
            
            # Process proxy endpoints
            print("  → Processing proxy endpoints...")
            for proxy_file in (self.apiproxy_dir / "proxies").glob("*.xml"):
                self._update_proxy_endpoint(proxy_file, temp_dir)
            
            # Process target endpoints
            print("  → Processing target endpoints...")
            for target_file in (self.apiproxy_dir / "targets").glob("*.xml"):
                self._update_target_endpoint(target_file, temp_dir)
            
            # Copy and update policies
            print("  → Processing policies...")
            self._copy_and_update_policies(temp_dir)
            
            # Copy resources
            print("  → Copying resources...")
            self._copy_resources(temp_dir)
            
            # Create ZIP bundle
            zip_path = output_path / f"{bundle_name}.zip"
            print(f"  → Creating bundle: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir.parent)
                        zipf.write(file_path, arcname)
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir.parent)
            
            print(f"\n✅ Bundle generated successfully: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            # Cleanup on error
            if temp_dir.parent.exists():
                shutil.rmtree(temp_dir.parent)
            raise RuntimeError(f"Failed to generate bundle: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Apigee X proxy bundle for Cropwise Unified Platform'
    )
    parser.add_argument(
        '--env', '-e',
        required=True,
        choices=['dev', 'qa', 'prod'],
        help='Target environment'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output directory for the bundle'
    )
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validate proxy structure before generating'
    )
    parser.add_argument(
        '--config', '-c',
        default=None,
        help='Path to environments.json configuration file'
    )
    
    args = parser.parse_args()
    
    # Determine base directory
    base_dir = Path(__file__).parent.parent
    
    try:
        generator = ProxyGenerator(
            base_dir=str(base_dir),
            env=args.env,
            config_path=args.config
        )
        
        if args.validate:
            if not generator.validate():
                sys.exit(1)
        
        bundle_path = generator.generate(args.output)
        print(f"\nBundle ready for deployment: {bundle_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
