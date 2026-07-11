PYTHON ?= python3
BUILD_DIR ?= build
DIST_DIR ?= dist
PYCACHE_DIR ?= /private/tmp/pl1compinpy-pycache

export PYTHONPATH := src

.PHONY: help clean compile docs test test-binary examples check build-text build-binaries build-libraries deliver

help:
	@printf '%s\n' 'PL1CompInPy make targets:'
	@printf '%s\n' '  make compile        - syntax-check source and tests'
	@printf '%s\n' '  make docs           - regenerate docs/API.md'
	@printf '%s\n' '  make test           - run the full unit test suite'
	@printf '%s\n' '  make test-binary    - run binary compile/result tests'
	@printf '%s\n' '  make examples       - parse and compile example coverage'
	@printf '%s\n' '  make build-text     - emit sample Python/JVM/.NET text outputs'
	@printf '%s\n' '  make build-binaries - emit sample PE/ELF/Mach-O binary containers'
	@printf '%s\n' '  make build-libraries- emit sample static/shared library containers'
	@printf '%s\n' '  make check          - run compile, docs, tests, binary tests, examples'
	@printf '%s\n' '  make deliver        - clean, check, build artifacts, and package dist tarball'

clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR) .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -type f -delete

compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE_DIR) $(PYTHON) -m compileall -q src tests scripts

docs:
	PYTHONPYCACHEPREFIX=$(PYCACHE_DIR) $(PYTHON) scripts/generate_api_docs.py

test:
	PYTHONPYCACHEPREFIX=$(PYCACHE_DIR) $(PYTHON) -m unittest discover -s tests

test-binary:
	PYTHONPYCACHEPREFIX=$(PYCACHE_DIR) $(PYTHON) -m unittest tests.test_binary_pipeline

examples:
	PYTHONPYCACHEPREFIX=$(PYCACHE_DIR) $(PYTHON) -m unittest tests.test_examples

check: compile docs test test-binary examples

build-text:
	mkdir -p $(BUILD_DIR)/text
	$(PYTHON) -m pl1compinpy examples/hello.pl1 --target python-source -o $(BUILD_DIR)/text/hello.py
	$(PYTHON) -m pl1compinpy examples/backend/jvm_bytecode.pl1 --target jvm-bytecode -o $(BUILD_DIR)/text/PL1Program.jasm
	$(PYTHON) -m pl1compinpy examples/backend/dotnet_il.pl1 --target dotnet-il -o $(BUILD_DIR)/text/PL1Program.il

build-binaries:
	mkdir -p $(BUILD_DIR)/bin
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format pe32-x586-windows -o $(BUILD_DIR)/bin/binary-entry-x586.exe
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format pe64-x86_64-windows -o $(BUILD_DIR)/bin/binary-entry-x64.exe
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format elf64-x86_64 -o $(BUILD_DIR)/bin/binary-entry-x86_64.elf
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format elf64-aarch64 -o $(BUILD_DIR)/bin/binary-entry-aarch64.elf
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format macho64-x86_64-macos -o $(BUILD_DIR)/bin/binary-entry-x86_64-macos
	$(PYTHON) -m pl1compinpy examples/backend/binary_entry.pl1 --emit binary --binary-format macho64-arm64-macos -o $(BUILD_DIR)/bin/binary-entry-arm64-macos

build-libraries:
	mkdir -p $(BUILD_DIR)/lib
	$(PYTHON) -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format static-ar -o $(BUILD_DIR)/lib/libmulti.a
	$(PYTHON) -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format shared-elf64 -o $(BUILD_DIR)/lib/libmulti.so
	$(PYTHON) -m pl1compinpy examples/language/multi_source_main.pl1 examples/language/module_helper.pl1 --emit library --library-format shared-pe64 -o $(BUILD_DIR)/lib/multi.dll

deliver: clean check build-text build-binaries build-libraries
	mkdir -p $(DIST_DIR)
	tar --exclude=.git --exclude=.venv --exclude=$(DIST_DIR) -czf $(DIST_DIR)/PL1CompInPy-delivery.tar.gz .
