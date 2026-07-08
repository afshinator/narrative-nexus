#!/bin/bash
export NN_DB_PATH=/project/narrative-nexus/data/demo/demo.db
export NN_READONLY=1
cd /project/narrative-nexus
exec uvicorn app.main:app --host 0.0.0.0 --port 3015 --reload
