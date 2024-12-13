#!/bin/bash

# 设置项目路径
CMDB_PATH="/home/jdo/cmdb"
FRONTEND_PATH="${CMDB_PATH}/ops-server"
BACKEND_PATH="${CMDB_PATH}/ops_api"
FRONTEND_LOG="${FRONTEND_PATH}/fe.log"
BACKEND_LOG="${BACKEND_PATH}/1.log"

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 定义日志查看函数
view_logs() {
    local log_type=$1
    local log_file
    local title
    
    case $log_type in
        "frontend")
            log_file=$FRONTEND_LOG
            title="Vue前端"
            ;;
        "backend")
            log_file=$BACKEND_LOG
            title="Django后端"
            ;;
    esac
    
    echo -e "\n=== $title 日志 ==="
    if [ -f "$log_file" ]; then
        echo -e "${YELLOW}按 q 退出日志查看并返回主菜单${NC}"
        echo -e "${YELLOW}按 Ctrl+C 中断日志跟踪并返回主菜单${NC}"
        
        # 使用 disown 确保 tail 进程不会受到 SIGINT 影响
        tail -f "$log_file" & 
        local tail_pid=$!
        disown $tail_pid
        
        # 等待用户按 Ctrl+C
        trap 'kill $tail_pid 2>/dev/null; return' SIGINT
        wait $tail_pid 2>/dev/null
        trap - SIGINT
    else
        error "日志文件不存在: $log_file"
        read -p "按回车键返回主菜单..."
    fi
}

# 检查前端是否成功启动
check_frontend_started() {
    local count=0
    local max_attempts=30  # 增加等待时间到30秒
    
    log "等待前端启动..."
    while [ $count -lt $max_attempts ]; do
        # 先检查npm进程
        if pgrep -f 'npm.*run dev' > /dev/null; then
            log "npm进程已启动"
            return 0
        fi
        
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    error "前端启动超时：未检测到npm进程"
    return 1
}

# 定义停止进程函数
stop_processes() {
    log "正在停止服务..."
    # 停止 npm 和 node 进程
    pkill -f 'npm.*run dev' && log "npm 进程已停止" || error "npm 进程未运行"
    pkill -f 'node.*vue-cli-service' && log "node 进程已停止" || error "node 进程未运行"
    pkill -f 'python3.*manage\.py.*runserver' && log "Django后端已停止" || error "Django后端未运行"
    sleep 2
}

# 定义启动进程函数
start_processes() {
    local is_restart=${1:-false}  # 添加参数来判断是否是重启操作
    log "正在启动服务..."
    local start_success=true
    
    # 启动Vue前端
    if [ -d "$FRONTEND_PATH" ]; then
        cd "$FRONTEND_PATH" || exit
        log "启动Vue前端..."
        
        # 确保之前的进程已经停止
        pkill -f 'npm.*run dev' 2>/dev/null
        pkill -f 'node.*vue-cli-service' 2>/dev/null
        sleep 2
        
        # 使用 setsid 启动前端服务，使其在新的会话中运行
        (setsid npm run dev -- --no-open &> "$FRONTEND_LOG" &)
        
        # 检查前端是否成功启动
        if check_frontend_started; then
            log "Vue前端启动成功"
        else
            error "Vue前端启动失败"
            start_success=false
        fi
    else
        error "前端目录不存在: $FRONTEND_PATH"
        start_success=false
    fi
    
    # 启动Django后端
    if [ -d "$BACKEND_PATH" ]; then
        cd "$BACKEND_PATH" || exit
        log "启动Django后端..."
        nohup python3 manage.py runserver 0.0.0.0:8000 > "$BACKEND_LOG" 2>&1 &
        sleep 2
        if pgrep -f 'python3.*manage\.py.*runserver' > /dev/null; then
            log "Django后端启动成功"
        else
            error "Django后端启动失败"
            start_success=false
        fi
    else
        error "后端目录不存在: $BACKEND_PATH"
        start_success=false
    fi
    
    if $start_success; then
        log "所有服务启动完成！"
        # 只在非重启时显示日志选项
        if ! $is_restart; then
            echo -e "\n${YELLOW}是否查看服务日志？${NC}"
            echo "1: 查看前端日志"
            echo "2: 查看后端日志"
            echo "n: 不查看"
            read -p "请选择: " view_choice
            case $view_choice in
                1) view_logs "frontend" ;;
                2) view_logs "backend" ;;
                *) return ;;
            esac
        fi
    else
        error "部分服务启动失败，请检查日志"
    fi
}

# 定义检查进程状态函数
check_status() {
    local npm_process=$(ps -ef | grep '[n]pm.*run dev')
    local node_process=$(ps -ef | grep '[n]ode.*vue-cli-service')
    local django_process=$(ps -ef | grep '[p]ython3 manage.py runserver')
    local frontend_running=false
    
    echo -e "\n当前服务状态："
    
    # 检查前端状态
    if [ -n "$npm_process" ] || [ -n "$node_process" ]; then
        # 检查日志中是否有运行地址信息
        if tail -n 50 "$FRONTEND_LOG" 2>/dev/null | grep -q "App running at:"; then
            echo -e "Vue前端: ${GREEN}运行中${NC}"
            frontend_running=true
        else
            echo -e "Vue前端: ${YELLOW}正在启动${NC}"
        fi
        
        # 显示进程信息
        [ -n "$npm_process" ] && echo "NPM 进程:" && echo "$npm_process"
        [ -n "$node_process" ] && echo "Node 进程:" && echo "$node_process"
    else
        echo -e "Vue前端: ${RED}未运行${NC}"
    fi
    
    # 检查后端状态
    if [ -n "$django_process" ]; then
        echo -e "Django后端: ${GREEN}运行中${NC}"
        echo "$django_process"
    else
        echo -e "Django后端: ${RED}未���行${NC}"
    fi
    
    # 如果前端正在运行，显示访问地址
    if $frontend_running; then
        echo -e "\n前端访问地址："
        tail -n 50 "$FRONTEND_LOG" | grep -A 2 "App running at:"
    fi
}

# 检查是否在 devbox 环境中
check_devbox_env() {
    if ! command -v devbox &> /dev/null; then
        error "devbox 未安装，跳过环境检查"
        return
    fi

    # 检查是否已经在 devbox 环境中
    if [[ "$DEVBOX_SHELL_ENABLED" != "1" ]]; then
        read -p "是否需要进入 devbox 环境？(y/n): " need_devbox
        if [[ "$need_devbox" == "y" ]]; then
            cd "$CMDB_PATH" || exit
            exec devbox shell "$0" "devbox_started"
        fi
    fi
}

# 服务管理主循环
service_management() {
    log "服务管理启动..."
    while true; do
        clear  # 清屏
        echo -e "\n${YELLOW}=== CMDB 服务管理菜单 ===${NC}"
        echo -e "当前目录: ${GREEN}$(pwd)${NC}"
        echo -e "当前用户: ${GREEN}$(whoami)${NC}"
        echo -e "\n选择操作"
        echo "1. 启动服务 (start)"
        echo "2. 重启服务 (restart)"
        echo "3. 查看状态 (status)"
        echo "4. 停止服务 (stop)"
        echo "5. 查看日志 (logs)"
        echo "6. 退出 (exit)"
        echo -e "\n${YELLOW}请输入选项 (1-6):${NC} \c"
        read choice
        
        case $choice in
            1)
                check_status
                if [ -n "$npm_process" ] || [ -n "$node_process" ] || [ -n "$django_process" ]; then
                    read -p "部分服务已在运行，是否继续启动？(y/n): " continue_start
                    if [[ "$continue_start" != "y" ]]; then
                        continue
                    fi
                fi
                start_processes
                read -p "按回车键继续..."
                ;;
            2)
                check_status
                stop_processes
                start_processes true  # 传入 true 表示这是重启操作
                read -p "按回车键继续..."
                ;;
            3)
                check_status
                read -p "按回车键继续..."
                ;;
            4)
                stop_processes
                read -p "按回车键继续..."
                ;;
            5)
                echo -e "\n选择要查看的日志："
                echo "1. Vue前端日志"
                echo "2. Django后端日志"
                read -p "请选择 (1/2): " log_choice
                case $log_choice in
                    1) view_logs "frontend" ;;
                    2) view_logs "backend" ;;
                    *) error "无效的选择" ;;
                esac
                read -p "按回车键继续..."
                ;;
            6)
                log "退出程序"
                exit 0
                ;;
            *)
                error "无效的选项，请重新选择"
                sleep 2
                ;;
        esac
    done
}

# 主程序入口
main() {
    log "主程序开始执行..."
    if [[ "$1" == "devbox_started" ]]; then
        log "从 devbox 环境启动..."
        service_management
    else
        log "检查 devbox 环境..."
        check_devbox_env
        service_management
    fi
}

# 确保脚本可执行
chmod +x "$0"

# 启动主程序
main "$@"