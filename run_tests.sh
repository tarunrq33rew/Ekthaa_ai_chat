#!/bin/bash

# Quick Test Runner - Real-World Testing for Product Discovery Chatbot
# Usage: bash run_tests.sh [option]

set -e

PROJECT_DIR="/Users/shiva/Documents/Ekthaa/AI/ chat-bot"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Function to print colored headers
print_header() {
    echo -e "\n${BOLD}${BLUE}═════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}${BLUE}  $1${RESET}"
    echo -e "${BOLD}${BLUE}═════════════════════════════════════════════════════════════${RESET}\n"
}

# Function to print step
print_step() {
    echo -e "${YELLOW}→${RESET} $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${RESET} $1"
}

# Check if server is running
check_server() {
    print_step "Checking if server is running on port 5001..."
    
    if nc -z localhost 5001 2>/dev/null; then
        print_success "Server is running"
        return 0
    else
        print_error "Server is NOT running"
        echo -e "\n${YELLOW}Start the server with:${RESET}"
        echo "  cd \"$BACKEND_DIR\""
        echo "  source \"$VENV_DIR/bin/activate\""
        echo "  python3 app.py"
        return 1
    fi
}

# Start server in background
start_server() {
    print_step "Starting server..."
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    python3 app.py > server.log 2>&1 &
    SERVER_PID=$!
    
    sleep 3
    
    if nc -z localhost 5001 2>/dev/null; then
        print_success "Server started (PID: $SERVER_PID)"
        return 0
    else
        print_error "Failed to start server"
        cat "$BACKEND_DIR/server.log" | head -20
        return 1
    fi
}

# Stop server
stop_server() {
    if [ ! -z "$SERVER_PID" ]; then
        print_step "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        sleep 1
        print_success "Server stopped"
    fi
}

# Run automated tests
run_automated_tests() {
    print_header "AUTOMATED TESTING"
    
    cd "$BACKEND_DIR"
    source "$VENV_DIR/bin/activate"
    
    if [ -f "test_real_world.py" ]; then
        print_step "Running test_real_world.py..."
        python3 test_real_world.py
        
        if [ -f "test_results_real_world.json" ]; then
            print_success "Test results saved to: test_results_real_world.json"
            
            # Show summary
            echo ""
            python3 << 'EOF'
import json
try:
    with open('test_results_real_world.json', 'r') as f:
        data = json.load(f)
        summary = data.get('summary', {})
        print(f"Summary: {summary['passed']}/{summary['total']} tests passed")
        if summary['pass_rate'] == 100:
            print("\033[92m✓ ALL TESTS PASSED!\033[0m")
        else:
            print(f"\033[93m⚠️  {summary['failed']} tests failed\033[0m")
except:
    pass
EOF
        fi
    else
        print_error "test_real_world.py not found"
        return 1
    fi
}

# Run manual curl tests
run_manual_tests() {
    print_header "MANUAL CURL TESTS"
    
    # Get JWT token
    print_step "Getting JWT token..."
    TOKEN_RESPONSE=$(curl -s -X POST http://localhost:5001/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"password123"}')
    
    TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$TOKEN" ]; then
        print_error "Failed to get JWT token"
        echo "Response: $TOKEN_RESPONSE"
        return 1
    fi
    
    print_success "Got JWT token: ${TOKEN:0:20}..."
    
    # Test 1: Product Query
    print_step "Test 1: Product Query (carpet search)"
    RESPONSE=$(curl -s -X POST http://localhost:5001/api/ai/chat \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message":"Where can I buy a carpet?","language":"en","conversation_id":"test1"}')
    
    if echo "$RESPONSE" | grep -q "product_search"; then
        print_success "Product query classified correctly"
    else
        print_error "Product query not classified correctly"
        echo "Response: $RESPONSE" | head -5
    fi
    
    # Test 2: Out-of-Scope (Financial)
    print_step "Test 2: Financial Query (out-of-scope rejection)"
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:5001/api/ai/chat \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message":"What do I owe?","language":"en","conversation_id":"test2"}')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "400" ]; then
        print_success "Financial query correctly rejected (HTTP 400)"
    else
        print_error "Financial query not rejected (got HTTP $HTTP_CODE)"
    fi
    
    # Test 3: Security (No Auth)
    print_step "Test 3: Security Test (missing JWT)"
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null -X POST http://localhost:5001/api/ai/chat \
        -H "Content-Type: application/json" \
        -d '{"message":"test","language":"en","conversation_id":"test3"}')
    
    if [ "$HTTP_CODE" = "401" ]; then
        print_success "Missing JWT correctly rejected (HTTP 401)"
    else
        print_error "Missing JWT not rejected (got HTTP $HTTP_CODE)"
    fi
}

# Show usage
show_usage() {
    cat << 'EOF'
Usage: bash run_tests.sh [option]

Options:
  auto      - Start server, run automated tests, then stop server
  manual    - Run manual cURL tests (server must be running)
  start     - Start the server only
  stop      - Stop the running server
  check     - Check if server is running
  logs      - Show server logs
  full      - Full test suite (auto + manual)
  help      - Show this help message

Examples:
  bash run_tests.sh auto      # Start server and run automated tests
  bash run_tests.sh manual    # Run manual tests (make sure server is running)
  bash run_tests.sh full      # Complete testing workflow
  bash run_tests.sh check     # Check server status

EOF
}

# Main script
case "${1:-help}" in
    auto)
        print_header "AUTOMATED TEST SUITE"
        if ! check_server; then
            if start_server; then
                trap stop_server EXIT
                run_automated_tests
            fi
        else
            run_automated_tests
        fi
        ;;
    
    manual)
        if check_server; then
            run_manual_tests
        else
            print_error "Server is not running. Start it with: bash run_tests.sh start"
            exit 1
        fi
        ;;
    
    start)
        start_server
        echo -e "\n${YELLOW}Server is running. Press Ctrl+C to stop.${RESET}"
        wait $SERVER_PID
        ;;
    
    stop)
        stop_server
        ;;
    
    check)
        check_server
        ;;
    
    logs)
        if [ -f "$BACKEND_DIR/server.log" ]; then
            print_header "SERVER LOGS"
            tail -50 "$BACKEND_DIR/server.log"
        else
            print_error "No server logs found"
        fi
        ;;
    
    full)
        print_header "FULL TEST SUITE"
        START_TIME=$(date +%s)
        
        if ! check_server; then
            if start_server; then
                SERVER_WAS_STARTED=true
            else
                print_error "Failed to start server"
                exit 1
            fi
        fi
        
        run_automated_tests
        run_manual_tests
        
        if [ "$SERVER_WAS_STARTED" = true ]; then
            stop_server
        fi
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        print_header "TEST SUITE COMPLETE"
        echo -e "Total time: ${DURATION}s\n"
        ;;
    
    help)
        show_usage
        ;;
    
    *)
        print_error "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
