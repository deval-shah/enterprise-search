#!/bin/bash
exec uvicorn llamasearch.main:app --host 0.0.0.0 --port 8000