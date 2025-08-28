"""
DICE™ Test Runner
Comprehensive test runner for all DICE algorithm components
"""

import pytest
import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DICETestRunner:
    """Test runner for DICE algorithm test suite"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.dice_test_dir = self.test_dir / "dice_algorithms"
        
    def run_all_tests(self, verbose=True, coverage=True):
        """Run all DICE algorithm tests"""
        args = [str(self.dice_test_dir)]
        
        if verbose:
            args.extend(["-v", "-s"])
            
        if coverage:
            args.extend([
                "--cov=app/services/dice_algorithms",
                "--cov=app/services/dice_orchestrator", 
                "--cov-report=html",
                "--cov-report=term-missing"
            ])
            
        # Add markers for different test types
        args.extend([
            "-m", "not integration",  # Skip integration tests by default
            "--tb=short"
        ])
        
        return pytest.main(args)
    
    def run_prescan_tests(self):
        """Run only PreScan Algorithm tests"""
        return pytest.main([
            str(self.dice_test_dir / "test_prescan_algorithm.py"),
            "-v"
        ])
    
    def run_ai_layer_1_tests(self):
        """Run only AI Layer 1 tests"""
        return pytest.main([
            str(self.dice_test_dir / "test_ai_layer_1.py"),
            "-v"
        ])
    
    def run_validation_tests(self):
        """Run only Validation Algorithm tests"""
        return pytest.main([
            str(self.dice_test_dir / "test_validation_algorithm.py"),
            "-v"
        ])
    
    def run_orchestrator_tests(self):
        """Run only DICE Orchestrator tests"""
        return pytest.main([
            str(self.dice_test_dir / "test_dice_orchestrator.py"),
            "-v"
        ])
    
    def run_integration_tests(self):
        """Run integration tests (requires full environment setup)"""
        return pytest.main([
            str(self.dice_test_dir),
            "-v",
            "-m", "integration",
            "--tb=long"
        ])
    
    def run_performance_tests(self):
        """Run performance benchmark tests"""
        return pytest.main([
            str(self.dice_test_dir),
            "-v", 
            "-k", "performance",
            "--tb=short"
        ])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DICE™ Algorithm Test Runner")
    parser.add_argument("--test-type", 
                       choices=["all", "prescan", "ai1", "validation", "orchestrator", "integration", "performance"],
                       default="all",
                       help="Type of tests to run")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    runner = DICETestRunner()
    
    if args.test_type == "all":
        exit_code = runner.run_all_tests(
            verbose=not args.quiet,
            coverage=not args.no_coverage
        )
    elif args.test_type == "prescan":
        exit_code = runner.run_prescan_tests()
    elif args.test_type == "ai1":
        exit_code = runner.run_ai_layer_1_tests()
    elif args.test_type == "validation":
        exit_code = runner.run_validation_tests()
    elif args.test_type == "orchestrator":
        exit_code = runner.run_orchestrator_tests()
    elif args.test_type == "integration":
        exit_code = runner.run_integration_tests()
    elif args.test_type == "performance":
        exit_code = runner.run_performance_tests()
    
    sys.exit(exit_code)
