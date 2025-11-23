#!/usr/bin/env python3
"""
Run Great Expectations Data Quality Checks
Payroll Analytics Platform

Usage:
    python run_data_quality_checks.py --checkpoint staging_checkpoint
    python run_data_quality_checks.py --checkpoint warehouse_checkpoint
    python run_data_quality_checks.py --all
"""

import sys
import argparse
from pathlib import Path

import great_expectations as gx
from great_expectations.checkpoint import Checkpoint


def run_checkpoint(context: gx.DataContext, checkpoint_name: str) -> bool:
    """Run a Great Expectations checkpoint.
    
    Args:
        context: Great Expectations data context
        checkpoint_name: Name of checkpoint to run
    
    Returns:
        True if validation passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Running Checkpoint: {checkpoint_name}")
    print(f"{'='*60}")
    
    try:
        # Get checkpoint
        checkpoint = context.get_checkpoint(checkpoint_name)
        
        # Run checkpoint
        result = checkpoint.run()
        
        # Check if validation passed
        if result["success"]:
            print(f"✅ {checkpoint_name} - PASSED")
            return True
        else:
            print(f"❌ {checkpoint_name} - FAILED")
            
            # Print failed expectations
            for validation_result in result.run_results.values():
                for expectation_result in validation_result["validation_result"]["results"]:
                    if not expectation_result["success"]:
                        print(f"   ❌ {expectation_result['expectation_config']['expectation_type']}")
                        if "observed_value" in expectation_result.get("result", {}):
                            print(f"      Observed: {expectation_result['result']['observed_value']}")
            
            return False
    
    except Exception as e:
        print(f"❌ Error running {checkpoint_name}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Great Expectations data quality checks")
    parser.add_argument(
        "--checkpoint",
        help="Name of checkpoint to run (staging_checkpoint, warehouse_checkpoint)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all checkpoints"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Initialize Great Expectations context
    print("📊 Initializing Great Expectations...")
    ge_dir = Path(__file__).parent.parent / "great_expectations"
    context = gx.get_context(context_root_dir=str(ge_dir))
    
    # Determine which checkpoints to run
    if args.all:
        checkpoints = ["staging_checkpoint", "warehouse_checkpoint"]
    elif args.checkpoint:
        checkpoints = [args.checkpoint]
    else:
        print("❌ Error: Must specify --checkpoint or --all")
        sys.exit(1)
    
    # Run checkpoints
    results = {}
    for checkpoint_name in checkpoints:
        success = run_checkpoint(context, checkpoint_name)
        results[checkpoint_name] = success
        
        if args.fail_fast and not success:
            print("\n🛑 Stopping due to failure (--fail-fast)")
            break
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for checkpoint_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{checkpoint_name}: {status}")
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    # Exit with appropriate code
    if failed > 0:
        print("\n❌ Data quality checks FAILED")
        sys.exit(1)
    else:
        print("\n✅ All data quality checks PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

