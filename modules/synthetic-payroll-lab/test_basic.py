#!/usr/bin/env python3
"""Basic test to verify package structure works."""

import sys
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("Testing synthetic-payroll-lab Package")
print("=" * 60)
print()

# Test 1: Import the package
print("✓ Test 1: Import package")
try:
    import synthetic_payroll_lab
    print(f"  → Package version: {synthetic_payroll_lab.__version__}")
    print("  → ✅ PASS")
except Exception as e:
    print(f"  → ❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 2: Import main classes
print("✓ Test 2: Import main classes")
try:
    from synthetic_payroll_lab import PayrollGenerator, ChaosConfig
    print("  → PayrollGenerator: OK")
    print("  → ChaosConfig: OK")
    print("  → ✅ PASS")
except Exception as e:
    print(f"  → ❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 3: Create generator instance
print("✓ Test 3: Create PayrollGenerator instance")
try:
    gen = PayrollGenerator(
        employees=100,
        start_date="2024-01-01",
        end_date="2024-01-07"
    )
    print(f"  → Employees: {gen.employees}")
    print(f"  → Date range: {gen.start_date.date()} to {gen.end_date.date()}")
    print("  → ✅ PASS")
except Exception as e:
    print(f"  → ❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 4: Create ChaosConfig
print("✓ Test 4: Create ChaosConfig instance")
try:
    chaos = ChaosConfig(
        duplicate_rate=0.05,
        null_spike_rate=0.02,
        late_arrival_pct=0.10
    )
    print(f"  → Duplicate rate: {chaos.duplicate_rate}")
    print(f"  → Null spike rate: {chaos.null_spike_rate}")
    print(f"  → Late arrival %: {chaos.late_arrival_pct}")
    print("  → ✅ PASS")
except Exception as e:
    print(f"  → ❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 5: Generate small dataset
print("✓ Test 5: Generate small test dataset")
try:
    output_path = Path(__file__).parent / "test_output"
    
    gen = PayrollGenerator(
        employees=10,  # Very small for testing
        start_date="2024-01-01",
        end_date="2024-01-07",
        seed=42  # For reproducibility
    )
    
    domains = gen.generate_all_domains(
        output_path=str(output_path),
        format="csv"
    )
    
    print(f"\n  → Generated {len(domains)} domains:")
    for domain_name, df in domains.items():
        print(f"     • {domain_name}: {len(df)} rows")
    
    print(f"\n  → Output directory: {output_path}")
    print("  → ✅ PASS")
    
except Exception as e:
    print(f"  → ❌ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("Package is working! Ready for full implementation.")
print()

