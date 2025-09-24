#!/usr/bin/env python3
"""
Environment Check and Fix Utility for Minecraft CV
==================================================

This utility diagnoses and fixes common environment issues that cause
VLC media player image loading errors and similar graphics problems.

Usage:
    python3 environment_check.py [--fix] [--verbose]

Common issues this fixes:
- VLC image demux errors: "Failed to load the image"
- Pyglet OpenGL initialization failures
- Missing X11 display in headless environments
- Missing OpenGL/GLU libraries
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

class EnvironmentChecker:
    """Comprehensive environment checker and fixer."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.issues = []
        self.fixes_applied = []
    
    def log(self, message, force=False):
        """Log message if verbose or force."""
        if self.verbose or force:
            print(message)
    
    def check_display_environment(self):
        """Check X11 display environment."""
        self.log("🖥️  Checking display environment...")
        
        display = os.environ.get('DISPLAY')
        if not display:
            self.issues.append({
                'type': 'display',
                'severity': 'warning',
                'message': 'No DISPLAY environment variable set',
                'fix': 'Set DISPLAY or use Xvfb for headless operation'
            })
            return False
        
        # Try to connect to display
        try:
            result = subprocess.run(['xdpyinfo'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log(f"✅ Display {display} is accessible")
                return True
            else:
                self.issues.append({
                    'type': 'display',
                    'severity': 'error',
                    'message': f'Cannot connect to display {display}',
                    'fix': 'Start X server or use Xvfb'
                })
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log("⚠️  Cannot verify display (xdpyinfo not available)")
            return True  # Assume it's okay if we can't check
    
    def check_xvfb_availability(self):
        """Check if Xvfb is available for headless operation."""
        self.log("🔍 Checking Xvfb availability...")
        
        if shutil.which('Xvfb'):
            self.log("✅ Xvfb is available")
            return True
        else:
            self.issues.append({
                'type': 'xvfb',
                'severity': 'warning',
                'message': 'Xvfb not available for headless graphics',
                'fix': 'Install Xvfb: sudo apt-get install xvfb'
            })
            return False
    
    def check_opengl_libraries(self):
        """Check OpenGL and GLU libraries."""
        self.log("🔧 Checking OpenGL libraries...")
        
        # Check for GLU library
        glu_found = False
        for lib_path in ['/usr/lib', '/usr/lib/x86_64-linux-gnu', '/usr/local/lib']:
            glu_libs = Path(lib_path).glob('*GLU*')
            if any(lib.is_file() for lib in glu_libs):
                glu_found = True
                break
        
        if not glu_found:
            self.issues.append({
                'type': 'opengl',
                'severity': 'error',
                'message': 'GLU library not found',
                'fix': 'Install GLU: sudo apt-get install libglu1-mesa libglu1-mesa-dev'
            })
            return False
        
        self.log("✅ OpenGL libraries appear to be available")
        return True
    
    def check_python_dependencies(self):
        """Check Python dependencies."""
        self.log("🐍 Checking Python dependencies...")
        
        required_packages = [
            ('pyglet', '1.5.27'),
            ('websockets', '12.0'),
            ('PIL', '8.0.0'),  # Pillow is imported as PIL
            ('numpy', '1.20.0')
        ]
        
        missing_packages = []
        for package, min_version in required_packages:
            try:
                __import__(package)
                self.log(f"✅ {package} is available")
            except ImportError:
                missing_packages.append(package)
                self.log(f"❌ {package} is missing")
        
        if missing_packages:
            self.issues.append({
                'type': 'python',
                'severity': 'error',
                'message': f'Missing Python packages: {", ".join(missing_packages)}',
                'fix': 'Install packages: pip install -r requirements.txt'
            })
            return False
        
        return True
    
    def check_texture_file(self):
        """Check if texture.png exists and is valid."""
        self.log("🖼️  Checking texture file...")
        
        texture_path = Path('texture.png')
        if not texture_path.exists():
            self.issues.append({
                'type': 'texture',
                'severity': 'error',
                'message': 'texture.png file is missing',
                'fix': 'Ensure texture.png is in the current directory'
            })
            return False
        
        # Check if it's a valid PNG
        try:
            with open(texture_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'\x89PNG'):
                    self.issues.append({
                        'type': 'texture',
                        'severity': 'error',
                        'message': 'texture.png is not a valid PNG file',
                        'fix': 'Replace texture.png with a valid PNG file'
                    })
                    return False
        except Exception as e:
            self.issues.append({
                'type': 'texture',
                'severity': 'error',
                'message': f'Cannot read texture.png: {e}',
                'fix': 'Check file permissions and integrity'
            })
            return False
        
        self.log("✅ texture.png is valid")
        return True
    
    def test_pyglet_functionality(self):
        """Test if Pyglet can initialize properly."""
        self.log("🎮 Testing Pyglet functionality...")
        
        try:
            # Try to import and test Pyglet
            import pyglet
            from pyglet import image
            
            # Try to create a minimal window (this will fail if display issues exist)
            # We'll catch the specific exception to diagnose the problem
            
            if not os.environ.get('DISPLAY'):
                self.log("⚠️  No DISPLAY set, Xvfb may be needed")
                return False
            
            # Try to load an image (this is what causes VLC-like errors)
            texture_path = Path('texture.png')
            if texture_path.exists():
                img = image.load(str(texture_path))
                self.log("✅ Pyglet can load images successfully")
                return True
            else:
                self.log("⚠️  Cannot test image loading without texture.png")
                return True
                
        except Exception as e:
            error_str = str(e)
            if 'Cannot connect to' in error_str or 'NoSuchDisplayException' in error_str:
                self.issues.append({
                    'type': 'pyglet',
                    'severity': 'error',
                    'message': 'Pyglet cannot connect to display',
                    'fix': 'Use xvfb-run or set up proper X11 display'
                })
            elif 'GLU' in error_str:
                self.issues.append({
                    'type': 'pyglet',
                    'severity': 'error',
                    'message': 'Pyglet missing GLU library',
                    'fix': 'Install GLU: sudo apt-get install libglu1-mesa-dev'
                })
            else:
                self.issues.append({
                    'type': 'pyglet',
                    'severity': 'error',
                    'message': f'Pyglet error: {error_str}',
                    'fix': 'Check dependencies and display environment'
                })
            return False
    
    def apply_fixes(self):
        """Apply automatic fixes where possible."""
        self.log("🔧 Applying automatic fixes...", force=True)
        
        for issue in self.issues:
            if issue['type'] == 'display' and not os.environ.get('DISPLAY'):
                # Try to start Xvfb
                if shutil.which('Xvfb'):
                    try:
                        # Check if Xvfb is already running on :99
                        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                        if 'Xvfb :99' not in result.stdout:
                            subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            import time
                            time.sleep(2)
                            os.environ['DISPLAY'] = ':99'
                            self.fixes_applied.append("Started Xvfb on :99")
                            print("✅ Started Xvfb virtual display")
                    except Exception as e:
                        print(f"⚠️  Could not start Xvfb: {e}")
    
    def run_full_check(self, apply_fixes=False):
        """Run all environment checks."""
        print("🏥 Running comprehensive environment check...\n")
        
        checks = [
            self.check_display_environment,
            self.check_xvfb_availability,
            self.check_opengl_libraries,
            self.check_python_dependencies,
            self.check_texture_file,
            self.test_pyglet_functionality
        ]
        
        for check in checks:
            check()
        
        if apply_fixes:
            self.apply_fixes()
        
        self.print_summary()
    
    def print_summary(self):
        """Print summary of issues and fixes."""
        print("\n" + "="*60)
        print("🏥 ENVIRONMENT CHECK SUMMARY")
        print("="*60)
        
        if not self.issues:
            print("🎉 No issues found! Environment is ready.")
            return
        
        # Group issues by severity
        errors = [i for i in self.issues if i['severity'] == 'error']
        warnings = [i for i in self.issues if i['severity'] == 'warning']
        
        if errors:
            print("\n❌ CRITICAL ISSUES (must be fixed):")
            for issue in errors:
                print(f"   • {issue['message']}")
                print(f"     Fix: {issue['fix']}")
        
        if warnings:
            print("\n⚠️  WARNINGS (recommended to fix):")
            for issue in warnings:
                print(f"   • {issue['message']}")
                print(f"     Fix: {issue['fix']}")
        
        if self.fixes_applied:
            print("\n🔧 FIXES APPLIED:")
            for fix in self.fixes_applied:
                print(f"   ✅ {fix}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Fix critical issues first")
        print("   2. Run with --fix to apply automatic fixes")
        print("   3. Use 'xvfb-run python3 launcher.py' for headless operation")
        print("   4. Install missing dependencies with 'pip install -r requirements.txt'")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Check and fix Minecraft CV environment')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker(verbose=args.verbose)
    checker.run_full_check(apply_fixes=args.fix)
    
    # Exit with non-zero code if critical issues found
    critical_issues = [i for i in checker.issues if i['severity'] == 'error']
    if critical_issues and not args.fix:
        print(f"\n❌ Found {len(critical_issues)} critical issue(s). Use --fix to attempt repairs.")
        sys.exit(1)
    elif critical_issues and args.fix:
        print(f"\n⚠️  Some critical issues may require manual intervention.")
        sys.exit(1)
    else:
        print("\n✅ Environment check completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()