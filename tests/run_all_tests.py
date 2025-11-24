#!/usr/bin/env python3
"""
Test runner for all Canvalo multi-agent system tests.

This script discovers and runs all test modules in the tests directory.
It provides a unified interface for running the entire test suite.

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --verbose    # Run with verbose output
    python tests/run_all_tests.py --test foundation  # Run specific test
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path
from typing import List, Tuple, Optional


class TestRunner:
    """Test runner for discovering and executing test modules."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tests_dir = Path(__file__).parent
        self.project_root = self.tests_dir.parent
        
        # Add project root to path for imports
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def discover_tests(self) -> List[Path]:
        """Discover all test modules in the tests directory."""
        test_files = []
        for file_path in self.tests_dir.glob("test_*.py"):
            if file_path.name != "test_runner.py":  # Exclude this file
                test_files.append(file_path)
        return sorted(test_files)
    
    def load_test_module(self, test_file: Path):
        """Load a test module dynamically."""
        module_name = test_file.stem
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        return None
    
    def run_test_module(self, test_file: Path) -> Tuple[str, bool, Optional[str]]:
        """
        Run a single test module.
        
        Returns:
            Tuple of (test_name, success, error_message)
        """
        test_name = test_file.stem.replace("test_", "").replace("_", " ").title()
        
        try:
            if self.verbose:
                print(f"\n{'=' * 60}")
                print(f"Running: {test_name}")
                print('=' * 60)
            
            module = self.load_test_module(test_file)
            if not module:
                return (test_name, False, "Failed to load module")
            
            # Look for main() function
            if hasattr(module, 'main'):
                result = module.main()
                success = result == 0
                return (test_name, success, None)
            else:
                return (test_name, False, "No main() function found")
                
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            if self.verbose:
                import traceback
                error_msg += f"\n{traceback.format_exc()}"
            return (test_name, False, error_msg)
    
    def run_all_tests(self, specific_test: Optional[str] = None) -> int:
        """
        Run all discovered tests or a specific test.
        
        Args:
            specific_test: Optional name of specific test to run
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        test_files = self.discover_tests()
        
        if not test_files:
            print("No test files found in tests directory")
            return 1
        
        # Filter for specific test if requested
        if specific_test:
            test_files = [
                f for f in test_files 
                if specific_test.lower() in f.stem.lower()
            ]
            if not test_files:
                print(f"No test found matching: {specific_test}")
                return 1
        
        print("=" * 60)
        print("CANVALO MULTI-AGENT SYSTEM - TEST SUITE")
        print("=" * 60)
        print(f"Discovered {len(test_files)} test module(s)")
        print()
        
        results = []
        for test_file in test_files:
            test_name, success, error = self.run_test_module(test_file)
            results.append((test_name, success, error))
            
            if not self.verbose:
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status}: {test_name}")
                if error and not success:
                    print(f"  Error: {error}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUITE SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_name, success, error in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
            if error and not success and not self.verbose:
                print(f"  Error: {error}")
        
        print(f"\nTotal: {passed}/{total} test modules passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test module(s) failed")
            return 1


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run Canvalo multi-agent system tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_all_tests.py                    # Run all tests
  python tests/run_all_tests.py --verbose          # Run with verbose output
  python tests/run_all_tests.py --test foundation  # Run specific test
  python tests/run_all_tests.py -v -t invoices    # Verbose + specific test
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '-t', '--test',
        type=str,
        help='Run a specific test (partial name match)'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    return runner.run_all_tests(specific_test=args.test)


if __name__ == "__main__":
    sys.exit(main())
