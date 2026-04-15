#!/bin/bash

# Backtest Debug Tool Wrapper
# 方便用戶運行 debug_backtest.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
TESTS_DIR="$PROJECT_ROOT/tests"

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印幫助信息
print_help() {
    cat << EOF
${BLUE}Backtest 調試工具${NC}

用法: $0 <符號> [選項]

位置參數:
  <符號>               要回測的符號（如 VTI, 0050.TW 等）
  
選項:
  -w, --weights        權重列表（如 "70 30" 用於兩個符號）
  -s, --start DATE     起始日期 (YYYY-MM-DD)，默認: 2年前
  -e, --end DATE       結束日期 (YYYY-MM-DD)，默認: 今天
  -h, --help           顯示此幫助信息

示例:
  # 單個符號
  $0 VTI -s 2020-01-01 -e 2024-01-01
  
  # 多個符號（等權）
  $0 VTI BND -s 2020-01-01 -e 2024-01-01
  
  # 多個符號（自定義權重）
  $0 VTI BND -w "70 30" -s 2020-01-01 -e 2024-01-01
  
  # 台灣股票
  $0 0050.TW 0056.TW -w "60 40" -s 2022-01-01 -e 2024-01-01
  
  # 全球 60/40 資產配置
  $0 VTI BND -w "60 40" -s 2018-01-01 -e 2024-01-01

EOF
}

# 檢查環境
check_environment() {
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${RED}❌ 後端目錄不存在: $BACKEND_DIR${NC}"
        exit 1
    fi
    
    if [ ! -f "$TESTS_DIR/debug_backtest.py" ]; then
        echo -e "${RED}❌ 調試腳本不存在: $TESTS_DIR/debug_backtest.py${NC}"
        exit 1
    fi
}

# 設置默認值
START_DATE=$(date -d "2 years ago" +%Y-%m-%d 2>/dev/null || date -v-2y +%Y-%m-%d 2>/dev/null || echo "2022-01-01")
END_DATE=$(date +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)
SYMBOLS=()
WEIGHTS=()

# 解析命令行參數
if [ $# -eq 0 ]; then
    print_help
    exit 0
fi

# 提取位置參數和選項
REMAINING_ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        -h|--help)
            print_help
            exit 0
            ;;
        -s|--start)
            ((i++))
            START_DATE="${!i}"
            ;;
        -e|--end)
            ((i++))
            END_DATE="${!i}"
            ;;
        -w|--weights)
            ((i++))
            WEIGHTS_STR="${!i}"
            IFS=' ' read -ra WEIGHTS <<< "$WEIGHTS_STR"
            ;;
        -*)
            echo -e "${RED}❌ 未知選項: $arg${NC}"
            print_help
            exit 1
            ;;
        *)
            REMAINING_ARGS+=("$arg")
            ;;
    esac
    ((i++))
done

# 最後的位置參數是符號
SYMBOLS=("${REMAINING_ARGS[@]}")

# 驗證輸入
if [ ${#SYMBOLS[@]} -eq 0 ]; then
    echo -e "${RED}❌ 必須指定至少一個符號${NC}"
    print_help
    exit 1
fi

# 驗證權重
if [ ${#WEIGHTS[@]} -gt 0 ] && [ ${#WEIGHTS[@]} -ne ${#SYMBOLS[@]} ]; then
    echo -e "${RED}❌ 權重數量必須等於符號數量${NC}"
    echo "符號數: ${#SYMBOLS[@]}, 權重數: ${#WEIGHTS[@]}"
    exit 1
fi

# 檢查環境
check_environment

# 打印配置
echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}Backtest 調試工具${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}配置:${NC}"
echo "  符號: ${SYMBOLS[*]}"
if [ ${#WEIGHTS[@]} -gt 0 ]; then
    echo "  權重: ${WEIGHTS[*]}"
fi
echo "  日期範圍: $START_DATE 至 $END_DATE"
echo ""

# 構建 Python 命令
PYTHON_ARGS=(
    "--symbols" "${SYMBOLS[@]}"
    "--start" "$START_DATE"
    "--end" "$END_DATE"
)

if [ ${#WEIGHTS[@]} -gt 0 ]; then
    PYTHON_ARGS+=("--weights" "${WEIGHTS[@]}")
fi

# 運行調試工具
echo -e "${YELLOW}正在運行調試工具...${NC}\n"

cd "$BACKEND"
python "$TESTS_DIR/debug_backtest.py" "${PYTHON_ARGS[@]}"

# 獲取退出代碼
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ 調試完成！${NC}"
    echo -e "📁 結果已保存到: ./temp/"
    echo -e "\n${YELLOW}生成的文件:${NC}"
    echo "  • backtest_raw_data_YYYY.csv — 每年的原始數據"
    echo "  • backtest_portfolio_value.csv — 組合價值曲線"
    echo "  • backtest_validation_report.json — JSON 格式報告"
    echo "  • backtest_validation_report.txt — 文本格式報告"
else
    echo -e "\n${RED}❌ 調試失敗 (退出代碼: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE
