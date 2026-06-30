# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 增强模块主脚本 (V1 → V3 CLI 包装)
# 委托到 V2 Pipeline 的 main() 函数

from core_workshop.pipelines.run_02_enhance.runner_v2 import main as v2_main

if __name__ == "__main__":
    v2_main()
