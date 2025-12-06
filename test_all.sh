#!/bin/bash

echo "Starting HR System Tests..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counter
PASSED=0
FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "

    response=$(curl -s "$url")

    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAILED${NC}"
        echo "Response: $response"
        ((FAILED++))
    fi
}

# Health checks
echo -e "${YELLOW}1. Health Checks${NC}"
test_endpoint "Backend Health" "http://localhost:8005/health" "ok"
test_endpoint "MCP Server Health" "http://localhost:8001/health" "ok"
echo ""

# MCP Tools
echo -e "${YELLOW}2. MCP Tools${NC}"
test_endpoint "MCP Tools List" "http://localhost:8001/tools/list" "search_jobs_multi_page"
test_endpoint "MCP Tools List (GitHub)" "http://localhost:8001/tools/list" "analyze_github"
echo ""

# HR Full Test
echo -e "${YELLOW}3. Full HR API Test${NC}"
echo -n "Testing Full HR API... "

if [ ! -f "test_hr_request.json" ]; then
    echo -e "${RED} FAILED${NC}"
    echo "test_hr_request.json not found!"
    ((FAILED++))
else
    response=$(curl -s -X POST http://localhost:8005/api/v1/hr/run \
      -H "Content-Type: application/json" \
      -d @test_hr_request.json)

    if echo "$response" | jq -e '.report.recommendations.shortlist' > /dev/null 2>&1; then
        echo -e "${GREEN} PASSED${NC}"
        ((PASSED++))

        # Validate specific fields
        echo -n "  - Checking processing_time_ms... "
        if echo "$response" | jq -e '.processing_time_ms' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking cache_stats... "
        if echo "$response" | jq -e '.cache_stats.hits' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking market_summary... "
        if echo "$response" | jq -e '.report.market_summary.total_found' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking market_insights... "
        if echo "$response" | jq -e '.report.market_insights.top_companies' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking candidate_scores... "
        if echo "$response" | jq -e '.report.candidate_scores[0]' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking activity_metrics... "
        if echo "$response" | jq -e '.report.candidate_scores[0].activity_metrics.days_since_last_push' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking decision_reasons... "
        if echo "$response" | jq -e '.report.candidate_scores[0].decision_reasons[0]' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

        echo -n "  - Checking recommendations... "
        if echo "$response" | jq -e '.report.recommendations.interview_next' > /dev/null 2>&1; then
            echo -e "${GREEN}${NC}"
        else
            echo -e "${RED}${NC}"
        fi

    else
        echo -e "${RED} FAILED${NC}"
        echo "Response: $response" | jq .
        ((FAILED++))
    fi
fi
echo ""

# Additional endpoints
echo -e "${YELLOW}4. Additional Endpoints${NC}"
echo -n "Testing Interview Endpoint... "
interview_response=$(curl -s "http://localhost:8005/api/v1/hr/interview/torvalds")
if echo "$interview_response" | jq -e '.script.questions' > /dev/null 2>&1; then
    echo -e "${GREEN} PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED} FAILED${NC}"
    ((FAILED++))
fi

echo -n "Testing Outreach Endpoint... "
outreach_response=$(curl -s "http://localhost:8005/api/v1/hr/outreach/torvalds?role=Backend%20Developer")
if echo "$outreach_response" | jq -e '.subject' > /dev/null 2>&1; then
    echo -e "${GREEN} PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED} FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo "========================================="
echo "            Test Summary"
echo "========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "========================================="
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! System is ready.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check the output above.${NC}"
    exit 1
fi
