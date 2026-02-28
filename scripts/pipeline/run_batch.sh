#!/bin/bash
set -e
# ============================================================================
# workshop 批量数据采集流水线运行脚本
# 自动处理指定目录下的所有 .bag 文件
# 用法：./scripts/pipeline/run_batch.sh <bag_directory> [--parallel <N>]
# 示例：./scripts/pipeline/run_batch.sh /partdata/raw --parallel 2
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/workshop_common.sh"

show_help() {
    echo "用法: $0 <bag目录> [选项]"
    echo ""
    echo "选项:"
    echo "  --parallel N      同时处理 N 个 bag 文件（默认 1，即串行）"
    echo "  --config CONFIG   指定配置文件路径（默认 /configs/pipeline_config.yaml）"
    echo "  -h, --help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 /partdata/raw"
    echo "  $0 /partdata/raw --parallel 2"
}

# 默认值
BAG_DIR=""
CONFIG_PATH="/configs/pipeline_config.yaml"
PARALLEL=1

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$BAG_DIR" ]; then
                BAG_DIR="$1"
                shift
            else
                log_error "未知参数: $1"
                show_help
                exit 1
            fi
            ;;
    esac
done

# 检查参数
if [ -z "$BAG_DIR" ]; then
    log_error "请指定 bag 文件目录"
    show_help
    exit 1
fi

if [ ! -d "$BAG_DIR" ]; then
    log_error "目录不存在: $BAG_DIR"
    exit 1
fi

# 检查并生成标定图像（全局一次）
PROJECT_ROOT="$(get_project_root)"
CALIB_IMAGES_DIR="$PROJECT_ROOT/partdata/calibration_images"
if [ -z "$(ls -A "$CALIB_IMAGES_DIR" 2>/dev/null)" ]; then
    log_warn "标定图像目录为空，将使用容器生成棋盘格图像..."
    docker run --rm -v "$PROJECT_ROOT:/workspace" workshop-base \
        python /workspace/scripts/utils/generate_realistic_calibration.py \
        --output /workspace/partdata/calibration_images
fi

# 获取所有 .bag 文件列表（支持 .bag 和 .bag 结尾的文件）
mapfile -t bag_files < <(find "$BAG_DIR" -maxdepth 1 -type f -name "*.bag" | sort)
if [ ${#bag_files[@]} -eq 0 ]; then
    log_error "目录 $BAG_DIR 中没有找到 .bag 文件"
    exit 1
fi

log_info "找到 ${#bag_files[@]} 个 bag 文件，并发数: $PARALLEL"

# 处理函数（对单个 bag 文件执行完整流水线）
process_one() {
    local bag_file="$1"
    local scene_id="scene_$(basename "$bag_file" .bag)_$(date +%Y%m%d_%H%M%S_%N)"
    log_info "开始处理: $bag_file -> $scene_id"

    # 调用 run_full.sh（假设它接受 bag 路径作为参数）
    "$SCRIPT_DIR/run_full.sh" --config "$CONFIG_PATH" "$bag_file" "$scene_id" || {
        log_error "处理失败: $bag_file"
        return 1
    }
    return 0
}

# 批量处理，控制并发
running=0
pids=()
for bag_file in "${bag_files[@]}"; do
    process_one "$bag_file" &
    pids+=($!)
    ((running++))

    # 如果达到并发上限，等待任意一个完成
    if [ $running -ge $PARALLEL ]; then
        wait -n  # 等待任意一个子进程结束
        # 重新计算 running 数量（清理已结束的进程）
        running=0
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                ((running++))
            fi
        done
    fi
done

# 等待所有剩余进程完成
wait

log_success "所有 bag 文件处理完成！"