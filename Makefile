IMG_PREFIX = message-it
VERSION ?= latest
PYTHON ?= 3.14

DOCKER_ARGS = --rm --interactive --tty

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

test: test-unit

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
