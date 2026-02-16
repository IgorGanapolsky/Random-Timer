#!/usr/bin/env bash
# assert.sh — Test assertion library for device tests
# Source this file after common.sh

PASS_COUNT=0
FAIL_COUNT=0
CURRENT_TEST=""

begin_test() {
  CURRENT_TEST="$1"
  echo -e "\n${CYAN}TEST: ${BOLD}$1${RESET}"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-Expected to contain '$needle'}"

  if echo "$haystack" | grep -q "$needle"; then
    echo -e "  ${GREEN}PASS${RESET}: $msg"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}FAIL${RESET}: $msg"
    echo -e "  ${RED}  Expected to find: $needle${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local msg="${3:-Expected NOT to contain '$needle'}"

  if echo "$haystack" | grep -q "$needle"; then
    echo -e "  ${RED}FAIL${RESET}: $msg"
    echo -e "  ${RED}  Unexpectedly found: $needle${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  else
    echo -e "  ${GREEN}PASS${RESET}: $msg"
    PASS_COUNT=$((PASS_COUNT + 1))
  fi
}

assert_eq() {
  local actual="$1"
  local expected="$2"
  local msg="${3:-Expected '$expected', got '$actual'}"

  if [ "$actual" = "$expected" ]; then
    echo -e "  ${GREEN}PASS${RESET}: $msg"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}FAIL${RESET}: $msg"
    echo -e "  ${RED}  Expected: $expected${RESET}"
    echo -e "  ${RED}  Actual:   $actual${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_not_empty() {
  local value="$1"
  local msg="${2:-Expected non-empty value}"

  if [ -n "$value" ]; then
    echo -e "  ${GREEN}PASS${RESET}: $msg"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}FAIL${RESET}: $msg"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

print_summary() {
  local total=$((PASS_COUNT + FAIL_COUNT))
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════${RESET}"
  echo -e "${BOLD}Results: ${GREEN}$PASS_COUNT passed${RESET}, ${RED}$FAIL_COUNT failed${RESET} (${total} total)"
  echo -e "${BOLD}═══════════════════════════════════════${RESET}"

  if [ "$FAIL_COUNT" -gt 0 ]; then
    return 1
  fi
  return 0
}
