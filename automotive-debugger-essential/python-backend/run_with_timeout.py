#!/usr/bin/env python3
"""
Timeout wrapper for running main.py with monitoring (Windows compatible)
"""
import subprocess
import time
import sys
import os
import threading
from threading import Timer

def run_with_timeout(timeout_seconds=30):
    """
    Run main.py with timeout monitoring (Windows compatible)
    """
    print(f"[MONITOR] Starting main.py with {timeout_seconds}s timeout...")
    print(f"[MONITOR] Expected startup time: ~10-15s, threshold: {timeout_seconds}s")
    
    start_time = time.time()
    process = None
    timeout_occurred = threading.Event()
    
    def timeout_handler():
        print(f"\n[TIMEOUT] Process exceeded {timeout_seconds}s, terminating...")
        timeout_occurred.set()
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    # Set up timeout timer
    timeout_timer = Timer(timeout_seconds, timeout_handler)
    timeout_timer.start()
    
    try:
        # Run main.py
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"[MONITOR] Process started with PID: {process.pid}")
        
        # Monitor output in real-time
        while True:
            if timeout_occurred.is_set():
                print("[TIMEOUT] Timeout occurred, exiting...")
                return 1
                
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                elapsed = time.time() - start_time
                print(f"[{elapsed:.1f}s] {output.strip()}")
                
                # Check for successful startup indicators
                if "Uvicorn running on" in output or "Application startup complete" in output:
                    print(f"[SUCCESS] Server started successfully in {elapsed:.1f}s")
                    timeout_timer.cancel()  # Cancel timeout
                    break
        
        # Wait for process to complete
        return_code = process.wait()
        elapsed = time.time() - start_time
        
        if return_code == 0:
            print(f"[SUCCESS] Process completed successfully in {elapsed:.1f}s")
        else:
            print(f"[ERROR] Process failed with return code {return_code} after {elapsed:.1f}s")
            
        return return_code
        
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] User interrupted after {time.time() - start_time:.1f}s")
        if process:
            process.terminate()
        return 1
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return 1
    finally:
        timeout_timer.cancel()

if __name__ == "__main__":
    # Default timeout: 30 seconds (20% threshold of expected 25s startup)
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    exit_code = run_with_timeout(timeout)
    sys.exit(exit_code)
