#!/bin/bash
# Test runner for Enterprise AI Support Agent

# Set PYTHONPATH to include src
export PYTHONPATH=/home/openclaw/Enterprise-AI-Support-Agent:$PYTHONPATH

# Run self-reflection tests (these should pass)
echo "Running self-reflection tests..."
pytest tests/test_self_reflection.py -v

# Run all tests (some may have issues)
echo "Running all tests..."
pytest tests/ -v