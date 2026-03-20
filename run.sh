#!/bin/bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib uvicorn app.main:app --reload --port 8000
