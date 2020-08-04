.PHONY: *

SERVICE_NAME := mapping
VERSION := $(shell git describe --tags)
CURRENT_DIR := $(shell pwd)
DOCKERFILE_PATH := deployment/Dockerfile

DOCKER_HUB_USERNAME := temdy

PROD_IMAGE_TAG := $(SERVICE_NAME):$(VERSION)
DEV_IMAGE_TAG := $(SERVICE_NAME)-dev:$(VERSION)
LINTING_IMAGE_TAG := $(SERVICE_NAME)-lint:$(VERSION)

TRUNCATED_VERSION := $(shell git describe --tags | tr "." "-")
HELM_RELEASE := $(SERVICE_NAME)-$(TRUNCATED_VERSION)

export DOCKER_BUILDKIT=1

help:  ## Print help and exit
	@echo Usage:
	@printf "  make \033[36m[target]\033[0m"
	@echo
	@echo Targets:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

v: build ## Display python, pip, and linux versions
	echo DOCKER VERSION=$(VERSION)
	docker run -it --rm \
		${PROD_IMAGE_TAG} \
		bash -c "cat /etc/*-release | grep VERSION= && python --version && pip --version"

cpr: ## Compile Python Requirements
	cd ${CURRENT_DIR}/requirements && make && cd ..

build:  ## Build the prod suitable docker container
	docker build \
		-f ${DOCKERFILE_PATH} \
		--target prod_image \
		-t ${PROD_IMAGE_TAG} \
		.

lint: build ## Find linting errors
	docker build \
		-f ${DOCKERFILE_PATH} \
		--target linting_image \
		-t $(LINTING_IMAGE_TAG) \
		.
	docker run -it --rm \
		-v ${CURRENT_DIR}:/code \
		${LINTING_IMAGE_TAG} \
		flake8 /code/src/

run-shell: build ## Run a shell insided the docker image
	docker run -it --rm \
		-v ${CURRENT_DIR}:/code \
		--env-file etc/.env \
		${PROD_IMAGE_TAG} \
		bash

push: ## Build the prod docker image and push it to docker hub
	docker login
	# --username ${DOCKER_HUB_USERNAME}
	make build
	docker tag ${PROD_IMAGE_TAG} ${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG}
	docker push ${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG}

hi: push  ## Install the helm chart (hi: helm install)
	helm install \
		-f ./deployment/helm-chart/values.yaml \
		-f ./deployment/helm-chart/secret-values.yaml \
		--set dockerImage=${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG} \
		${HELM_RELEASE} \
		./deployment/helm-chart/
	./deployment/script.sh

hu:  ## Un-install the helm chart (hu: helm uninstall)
	helm uninstall ${HELM_RELEASE}
