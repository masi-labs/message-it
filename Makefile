IMG_PREFIX = message-it
VERSION ?= latest
PYTHON ?= 3.14
EXE_NAME ?= message-it
EXE_ENTRY ?= message-it.py
PACKAGER_PYTHON ?= python

DOCKER_ARGS = --rm --interactive --tty

DC_ITEST = docker compose -f docker-compose.itest.yml

ifeq ($(CI),true)
	# Github Actions doesn't provide a TTY
	DOCKER_ARGS = --rm
endif

DOCKER_RUN = docker container run \
	$(DOCKER_ARGS) \
	$(addprefix --volume ,$(VOLUMES))

RUNNER = $(DOCKER_RUN) '$(IMG_PREFIX)-runner:$(VERSION)'

.PHONY: default

default: runner test lint typecheck

clean:
	docker image rm '$(IMG_PREFIX)-runner:$(VERSION)'

.PHONY: runner test test-unit lint lint-src lint-tests typecheck
.PHONY: test-integration itest-up itest-down
.PHONY: exe-macos-arm64 exe-macos-x86_64

test: test-unit test-integration

.PHONY: test-integration itest-up itest-down

mock-up:
	$(DC_ITEST) up -d --build receiver
	$(DC_ITEST) logs -f receiver

mock-down:
	$(DC_ITEST) down -v

test-integration:
	@set -e; \
		$(DC_ITEST) up -d --build receiver; \
		rc=0; \
		$(DC_ITEST) run --rm tests || rc=$$?; \
		$(DC_ITEST) down -v; \
		exit $$rc

test-integration-ci:
	@set -e; \
		rc=0; \
		$(DC_ITEST) up --build --abort-on-container-exit --exit-code-from tests || rc=$$?; \
		$(DC_ITEST) down -v; \
		exit $$rc

runner:
	DOCKER_BUILDKIT=1 docker build \
		--ssh default \
		--build-arg 'PYTHON=$(PYTHON)' \
		--tag '$(IMG_PREFIX)-$@:$(VERSION)' \
		--file tests/Dockerfile \
		.

test-unit: VOLUMES += '$(PWD)/src:/code/src'
test-unit: VOLUMES += '$(PWD)/tests:/code/tests'
test-unit: TEST_PATH = tests/unit
test-unit:
	$(RUNNER) pytest -p no:cacheprovider $(TEST_PATH)

lint: lint-src lint-tests

lint-src: VOLUMES += '$(PWD)/src:/code/src'
lint-src:
	$(RUNNER) pylint --rcfile=src/.pylintrc src/

lint-tests: VOLUMES += '$(PWD)/src:/code/src'
lint-tests: VOLUMES += '$(PWD)/tests:/code/tests'
lint-tests:
	$(RUNNER) pylint --rcfile=tests/.pylintrc tests/

typecheck: VOLUMES += '$(PWD)/src:/code/src'
typecheck:
	$(RUNNER) mypy --config-file=src/mypy.ini src/

exe-macos-arm64:
	arch -arm64 $(PACKAGER_PYTHON) -m PyInstaller --clean --onefile --name '$(EXE_NAME)' '$(EXE_ENTRY)'

exe-macos-x86_64:
	arch -x86_64 $(PACKAGER_PYTHON) -m PyInstaller --clean --onefile --name '$(EXE_NAME)' '$(EXE_ENTRY)'
