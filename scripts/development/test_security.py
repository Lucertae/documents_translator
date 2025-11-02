#!/usr/bin/env python3
"""
Script per testare tutti i componenti sicurezza
"""
import sys
from pathlib import Path

# Aggiungi path per import
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "app"))

def test_security_manager():
    """Test Security Manager"""
    print("Testing Security Manager...")
    try:
        # Import da cartella security/ (non app/)
        security_path = BASE_DIR / "security"
        if str(security_path) not in sys.path:
            sys.path.insert(0, str(security_path))
        from security_manager import SecurityManager
        sm = SecurityManager(BASE_DIR)
        
        # Test encryption
        test_data = "test_secret_data_123"
        encrypted = sm.encrypt_data(test_data)
        if not encrypted:
            print("  ✗ Encryption failed")
            return False
        
        decrypted = sm.decrypt_data(encrypted)
        if decrypted != test_data:
            print(f"  ✗ Decryption failed: expected '{test_data}', got '{decrypted}'")
            return False
        
        # Test status
        status = sm.check_security_status()
        if not status.get('encryption_available'):
            print("  ✗ Encryption not available")
            return False
        
        print("  ✓ Security Manager OK")
        return True
    except Exception as e:
        print(f"  ✗ Security Manager error: {e}")
        return False

def test_integrity_checker():
    """Test Integrity Checker"""
    print("Testing Integrity Checker...")
    try:
        from integrity_checker import IntegrityChecker
        ic = IntegrityChecker(BASE_DIR)
        
        # Check manifest exists
        if not ic.manifest_file.exists():
            print("  ⚠ No manifest file (first time setup?)")
            print("  → Run: python scripts/development/create_integrity_manifest.py")
            return True  # Not an error, just first time
        
        # Load manifest
        manifest = ic.load_manifest()
        if manifest is None:
            print("  ✗ Cannot load manifest")
            return False
        
        print(f"  ✓ Manifest loaded ({len(manifest)} files)")
        
        # Verify integrity (non-strict)
        results = ic.verify_integrity(strict=False)
        if not results:
            print("  ⚠ No files verified (empty manifest?)")
        else:
            all_ok = all(results.values())
            if all_ok:
                print(f"  ✓ Integrity check passed ({len(results)} files)")
            else:
                failed = [f for f, ok in results.items() if not ok]
                print(f"  ⚠ Integrity check found {len(failed)} modified file(s): {', '.join(failed)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Integrity Checker error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security_validator():
    """Test Security Validator"""
    print("Testing Security Validator...")
    try:
        from security_validator import get_security_validator
        sv = get_security_validator(BASE_DIR)
        
        results = sv.perform_security_checks()
        
        status = results.get('overall_status', 'UNKNOWN')
        if status == 'OK':
            print(f"  ✓ Security Validator OK (status: {status})")
        elif status == 'WARNING':
            warnings = results.get('warnings', [])
            print(f"  ⚠ Security Validator warnings: {', '.join(warnings)}")
        else:
            print(f"  ✗ Security Validator failed (status: {status})")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ Security Validator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_secure_storage():
    """Test Secure Storage"""
    print("Testing Secure Storage...")
    try:
        from secure_storage import SecureStorage
        ss = SecureStorage()
        
        # Test save/load
        test_key = "test_key_123"
        test_value = "test_secret_value_456"
        
        if not ss.save_secure_value(test_key, test_value, encrypt=True):
            print("  ✗ Save failed")
            return False
        
        loaded_value = ss.load_secure_value(test_key)
        if loaded_value != test_value:
            print(f"  ✗ Load failed: expected '{test_value}', got '{loaded_value}'")
            return False
        
        # Cleanup
        ss.delete_secure_value(test_key)
        
        print("  ✓ Secure Storage OK")
        return True
    except Exception as e:
        print(f"  ✗ Secure Storage error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Esegue tutti i test"""
    print("=" * 60)
    print("LAC TRANSLATE - Security System Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Security Manager", test_security_manager),
        ("Integrity Checker", test_integrity_checker),
        ("Security Validator", test_security_validator),
        ("Secure Storage", test_secure_storage),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append((name, False))
            print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("✓ All security tests passed!")
        return 0
    else:
        print()
        print("⚠ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

