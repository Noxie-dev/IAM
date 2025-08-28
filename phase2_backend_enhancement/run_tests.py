#!/usr/bin/env python3
"""
Test Runner for Audio Enhancement Features
Phase 2: Backend Enhancement

Comprehensive test runner with different test suites and reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for audio enhancement features"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a command and return success status"""
        print(f"\n🔄 {description}")
        print(f"Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {description} - SUCCESS")
                return True
            else:
                print(f"❌ {description} - FAILED (exit code: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check if test dependencies are installed"""
        print("🔍 Checking test dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "soundfile",
            "numpy",
            "librosa"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install -r requirements-test.txt")
            return False
        
        print("✅ All test dependencies are installed")
        return True
    
    def run_unit_tests(self) -> bool:
        """Run unit tests only"""
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "not integration",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running unit tests")
    
    def run_integration_tests(self) -> bool:
        """Run integration tests (requires external services)"""
        print("\n⚠️  Integration tests require:")
        print("   - OpenAI API key (OPENAI_API_KEY)")
        print("   - S3/Wasabi credentials (S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET_NAME)")
        
        # Check for required environment variables
        required_env = ["OPENAI_API_KEY", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET_NAME"]
        missing_env = [var for var in required_env if not os.getenv(var)]
        
        if missing_env:
            print(f"⚠️  Missing environment variables: {', '.join(missing_env)}")
            print("   Integration tests will be skipped")
        
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "integration",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running integration tests")
    
    def run_audio_tests(self) -> bool:
        """Run audio processing specific tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_audio_enhancement.py",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running audio enhancement tests")
    
    def run_storage_tests(self) -> bool:
        """Run storage service tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_storage_service.py",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running storage service tests")
    
    def run_transcription_tests(self) -> bool:
        """Run transcription service tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_transcription_service.py",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running transcription service tests")
    
    def run_endpoint_tests(self) -> bool:
        """Run API endpoint tests"""
        command = [
            "python", "-m", "pytest",
            "tests/test_transcription_endpoints.py",
            "-v",
            "--tb=short"
        ]
        
        return self.run_command(command, "Running API endpoint tests")
    
    def run_all_tests(self) -> bool:
        """Run all tests with coverage"""
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ]
        
        return self.run_command(command, "Running all tests with coverage")
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks"""
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "slow",
            "-v",
            "--tb=short",
            "--benchmark-only"
        ]
        
        return self.run_command(command, "Running performance tests")
    
    def generate_test_report(self) -> bool:
        """Generate comprehensive test report"""
        command = [
            "python", "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--html=test_report.html",
            "--self-contained-html"
        ]
        
        success = self.run_command(command, "Generating test report")
        
        if success:
            print("\n📊 Test reports generated:")
            print(f"   - HTML Coverage: {self.project_root}/htmlcov/index.html")
            print(f"   - Test Report: {self.project_root}/test_report.html")
        
        return success
    
    def lint_code(self) -> bool:
        """Run code linting"""
        commands = [
            (["python", "-m", "flake8", "app/", "tests/"], "Running flake8 linting"),
            (["python", "-m", "black", "--check", "app/", "tests/"], "Running black formatting check"),
            (["python", "-m", "isort", "--check-only", "app/", "tests/"], "Running isort import check"),
        ]
        
        all_passed = True
        for command, description in commands:
            if not self.run_command(command, description):
                all_passed = False
        
        return all_passed
    
    def fix_formatting(self) -> bool:
        """Fix code formatting"""
        commands = [
            (["python", "-m", "black", "app/", "tests/"], "Fixing code formatting with black"),
            (["python", "-m", "isort", "app/", "tests/"], "Fixing import order with isort"),
        ]
        
        all_passed = True
        for command, description in commands:
            if not self.run_command(command, description):
                all_passed = False
        
        return all_passed


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Audio Enhancement Test Runner")
    parser.add_argument(
        "suite",
        nargs="?",
        choices=[
            "unit", "integration", "audio", "storage", 
            "transcription", "endpoints", "all", "performance",
            "report", "lint", "format"
        ],
        default="unit",
        help="Test suite to run (default: unit)"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check test dependencies before running"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🎵 Audio Enhancement Test Runner")
    print("=" * 50)
    
    # Check dependencies if requested
    if args.check_deps:
        if not runner.check_dependencies():
            sys.exit(1)
    
    # Run selected test suite
    success = False
    
    if args.suite == "unit":
        success = runner.run_unit_tests()
    elif args.suite == "integration":
        success = runner.run_integration_tests()
    elif args.suite == "audio":
        success = runner.run_audio_tests()
    elif args.suite == "storage":
        success = runner.run_storage_tests()
    elif args.suite == "transcription":
        success = runner.run_transcription_tests()
    elif args.suite == "endpoints":
        success = runner.run_endpoint_tests()
    elif args.suite == "all":
        success = runner.run_all_tests()
    elif args.suite == "performance":
        success = runner.run_performance_tests()
    elif args.suite == "report":
        success = runner.generate_test_report()
    elif args.suite == "lint":
        success = runner.lint_code()
    elif args.suite == "format":
        success = runner.fix_formatting()
    
    # Print summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
