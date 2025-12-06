#!/bin/bash

echo "=== HR Recruitment System Tests ==="
echo ""

# Test 1: Simple case (only Python required)
echo "Test 1: Python Developer (only Python mandatory)"
echo "Expected: GVanRossum=GO, Torvalds=NO"
echo ""
curl -s -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_simple.json | \
  jq -r '.report.candidate_scores[] | "  \(.github_username): score=\(.score), decision=\(.decision), mandatory_coverage=\(.requirement_match.mandatory_coverage)%"'
echo ""

# Test 2: Full case (Python + FastAPI + Docker + PostgreSQL + Redis + K8s mandatory)
echo "Test 2: Senior Backend Developer (6 mandatory skills)"
echo "Expected: All candidates rejected (missing FastAPI/Docker/etc)"
echo ""
curl -s -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | \
  jq -r '.report.candidate_scores[] | "  \(.github_username): score=\(.score), decision=\(.decision), mandatory_coverage=\(.requirement_match.mandatory_coverage)%"'
echo ""

# Test 3: Skill classification check
echo "Test 3: Skill Classification (Full request)"
echo ""
curl -s -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | \
  jq '.report.skill_classification_report.summary'
echo ""

# Test 4: Detailed reasons for one candidate
echo "Test 4: Detailed Rejection Reasons (Torvalds)"
echo ""
curl -s -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | \
  jq '.report.candidate_scores[] | select(.github_username == "torvalds") | {username: .github_username, score, decision, decision_reasons, requirement_match: {mandatory_coverage: .requirement_match.mandatory_coverage, mandatory_missing: .requirement_match.mandatory_missing}}'
echo ""

echo "Tests complete!"
