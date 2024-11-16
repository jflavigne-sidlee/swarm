from tests.test_basic_handoff import test_basic_handoff
from tests.test_context_variables import test_context_variables
from tests.test_function_calling import test_function_calling

def run_all_tests():
    print("Running all Swarm tests...")
    
    try:
        test_basic_handoff()
        print("✓ Basic handoff test passed")
    except Exception as e:
        print(f"✗ Basic handoff test failed: {str(e)}")
    
    try:
        test_context_variables()
        print("✓ Context variables test passed")
    except Exception as e:
        print(f"✗ Context variables test failed: {str(e)}")
    
    try:
        test_function_calling()
        print("✓ Function calling test passed")
    except Exception as e:
        print(f"✗ Function calling test failed: {str(e)}")

if __name__ == "__main__":
    run_all_tests() 