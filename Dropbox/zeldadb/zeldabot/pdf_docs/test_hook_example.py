#!/usr/bin/env python3
"""
Simple test file to demonstrate hook functionality.
This file will trigger the PostToolUse hook when Claude writes/edits it.
"""

def hello_hooks():
    print("This is a test function to see hooks in action!")
    return "Hooks are working!"

if __name__ == "__main__":
    print("Testing Claude Code hooks...")
    result = hello_hooks()
    print(result)