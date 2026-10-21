# ANSI color codes
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
BLUE=\033[0;34m
RESET=\033[0m

PYTHON=uv run python
TEST=uv run pytest
PROJECT_ROOT=.

########################################################
# Check dependencies
########################################################

UV_MIN_VERSION=0.13.4

check_uv:
	@echo "$(YELLOW)🔍Checking uv version...$(RESET)"
	@if ! command -v uv > /dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv before proceeding.$(RESET)"; \
		exit 1; \
	fi; \
	version=$$(uv --version | awk '{print $$2}'); \
	if ! awk -v min="$(UV_MIN_VERSION)" -v got="$$version" 'BEGIN { split(min, m, "."); split(got, g, "."); for (i = 1; i <= 3; i++) { if ((g[i] + 0) != (m[i] + 0)) exit ((g[i] + 0) > (m[i] + 0) ? 0 : 1) } exit 0 }'; then \
		echo "$(RED)uv $$version is older than the required $(UV_MIN_VERSION). Run 'uv self update'.$(RESET)"; \
		exit 1; \
	fi; \
	uv --version

check_jq:
	@echo "$(YELLOW)🔍Checking jq version...$(RESET)"
	@if ! command -v jq > /dev/null 2>&1; then \
		echo "$(RED)jq is not installed. Please install jq before proceeding.$(RESET)"; \
		echo "$(RED)brew install jq$(RESET)"; \
		exit 1; \
	else \
		jq --version; \
	fi

########################################################
# Setup githooks for linting
########################################################
setup_githooks:
	@echo "$(YELLOW)🔨Setting up githooks on post-commit...$(RESET)"
	chmod +x .githooks/post-commit
	git config core.hooksPath .githooks


########################################################
# Python dependency-related
########################################################

update_python_dep: check_uv
	@echo "$(YELLOW)🔄Updating python dependencies...$(RESET)"
	@uv sync

view_python_venv_size:
	@echo "$(YELLOW)🔍Checking python venv size...$(RESET)"
	@PYTHON_VERSION=$$(cat .python-version | cut -d. -f1,2) && \
	cd .venv/lib/python$$PYTHON_VERSION/site-packages && du -sh . && cd ../../../
	@echo "$(GREEN)Python venv size check completed.$(RESET)"

view_python_venv_size_by_libraries:
	@echo "$(YELLOW)🔍Checking python venv size by libraries...$(RESET)"
	@PYTHON_VERSION=$$(cat .python-version | cut -d. -f1,2) && \
	cd .venv/lib/python$$PYTHON_VERSION/site-packages && du -sh * | sort -h && cd ../../../
	@echo "$(GREEN)Python venv size by libraries check completed.$(RESET)"

########################################################
# Run Main Application
########################################################

all: update_python_dep setup_githooks
	@echo "$(GREEN)🏁Running main application...$(RESET)"
	@$(PYTHON) main.py
	@echo "$(GREEN)✅ Main application run completed.$(RESET)"

########################################################
# Demo
########################################################

show-mobile-screen:
	@echo "$(YELLOW)🏁Showing mobile screen...$(RESET)"
	adb exec-out screenrecord --output-format=h264 - | \
	ffplay -framerate 60 -probesize 32 -x 480 -y 960 -sync video -


demo:
	@echo "$(YELLOW)🏁Starting demo...$(RESET)"
	@$(PYTHON) -m src.demo.demo
	@echo "$(GREEN)✅ Demo started.$(RESET)"


########################################################
# Run Tests
########################################################

TEST_TARGETS = tests/

# Tests
test: check_uv
	@echo "$(GREEN)🧪Running Target Tests...$(RESET)"
	$(TEST) $(TEST_TARGETS)
	@echo "$(GREEN)✅Target Tests Passed.$(RESET)"


########################################################
# Cleaning
########################################################

# Linter will ignore these directories
IGNORE_LINT_DIRS = .venv|venv
LINE_LENGTH = 88

lint: check_uv check_jq
	@echo "$(YELLOW)✨Linting project with Black...$(RESET)"
	@uv run black --exclude '/($(IGNORE_LINT_DIRS))/' . --line-length $(LINE_LENGTH)
	@echo "$(YELLOW)✨Linting and formatting JSONs with jq...$(RESET)"
	@count=0; \
	find . \( $(IGNORE_LINT_DIRS:%=-path './%' -prune -o) \) -type f -name '*.json' -print0 | \
	while IFS= read -r -d '' file; do \
		if jq . "$$file" > "$$file.tmp" 2>/dev/null && mv "$$file.tmp" "$$file"; then \
			count=$$((count + 1)); \
		else \
			rm -f "$$file.tmp"; \
		fi; \
	done; \
	echo "$(BLUE)$$count JSON file(s)$(RESET) linted and formatted."; \
	echo "$(GREEN)✅Linting completed.$(RESET)"

vulture: check_uv
	@echo "$(YELLOW)🔍Running Vulture...$(RESET)"
	@uv run vulture .
	@echo "$(GREEN)✅Vulture completed.$(RESET)"

########################################################
# Dependencies
########################################################

requirements: check_uv
	@echo "$(YELLOW)🔍Checking requirements...$(RESET)"
	@uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
	@echo "$(GREEN)✅Requirements checked.$(RESET)"
