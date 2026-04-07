# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".

set -e
cd "$(dirname "$0")/../.."
pytest tests/unit -v --cov=pipelines --cov-report=html