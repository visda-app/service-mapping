.PHONY: *

SERVICE_NAME := mapping
SERVICE_PORT := 5001
VERSION := $(shell git describe --tags)
CURRENT_DIR := $(shell pwd)
DOCKERFILE_PATH := deployment/Dockerfile

DOCKER_HUB_USERNAME := temdy

PROD_IMAGE_TAG := ${SERVICE_NAME}:$(VERSION)
DEV_IMAGE_TAG := ${SERVICE_NAME}-dev:$(VERSION)
LINTING_IMAGE_TAG := ${SERVICE_NAME}-lint:$(VERSION)

TRUNCATED_VERSION := $(shell git describe --tags | tr "." "-")
HELM_RELEASE := ${SERVICE_NAME} # -$(TRUNCATED_VERSION)

TEST=

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

build-dev:  ## Build the prod suitable docker container
	docker build \
		-f ${DOCKERFILE_PATH} \
		--target dev_image \
		-t ${DEV_IMAGE_TAG} \
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

run-shell: build-dev ## Run a shell insided the docker image
	docker run -it --rm \
		-v ${CURRENT_DIR}:/code \
		--env-file etc/.env \
		${DEV_IMAGE_TAG} \
		bash

run: build ## Run a server in the prod docker image
	docker run -it --rm \
		-v ${CURRENT_DIR}/src:/code/src \
		--env-file etc/.env \
		-p ${SERVICE_PORT}:${SERVICE_PORT} \
		${PROD_IMAGE_TAG} \
		gunicorn route:app -c configs/gunicorn_configs.py

push: ## Build the prod docker image and push it to docker hub
	docker login
	# --username ${DOCKER_HUB_USERNAME}
	make build
	docker tag ${PROD_IMAGE_TAG} ${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG}
	docker push ${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG}

push-dev: ## Build the prod docker image and push it to docker hub
	docker login
	# --username ${DOCKER_HUB_USERNAME}
	make build-dev
	docker tag ${DEV_IMAGE_TAG} ${DOCKER_HUB_USERNAME}/${DEV_IMAGE_TAG}
	docker push ${DOCKER_HUB_USERNAME}/${DEV_IMAGE_TAG}

hi: push  ## Install the helm chart (hi: helm install)
	helm install \
		-f ./deployment/${SERVICE_NAME}/values.yaml \
		-f ./deployment/${SERVICE_NAME}/secret-values.yaml \
		--set dockerImage=${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG} \
		${HELM_RELEASE} \
		./deployment/${SERVICE_NAME}/

ht:  ## Shows the Helm template
	helm template \
		-f ./deployment/${SERVICE_NAME}/values.yaml \
		-f ./deployment/${SERVICE_NAME}/secret-values.yaml \
		--set dockerImage=${DOCKER_HUB_USERNAME}/${PROD_IMAGE_TAG} \
		${HELM_RELEASE} \
		./deployment/${SERVICE_NAME}/

hide: push-dev  ## Install the helm chart (hide: helm install dev)
	helm install \
		-f ./deployment/${SERVICE_NAME}/values.yaml \
		-f ./deployment/${SERVICE_NAME}/secret-values.yaml \
		--set dockerImage=${DOCKER_HUB_USERNAME}/${DEV_IMAGE_TAG} \
		${HELM_RELEASE} \
		./deployment/${SERVICE_NAME}/

hu:  ## Un-install the helm chart (hu: helm uninstall)
	helm uninstall ${HELM_RELEASE}


notebook: build-dev ## Run the jupyter notebook in docker
	docker run -it --rm \
		-v ${CURRENT_DIR}:/code \
		-p 8888:8888 \
		-u 0 \
		${DEV_IMAGE_TAG} \
		jupyter notebook \
			--ip 0.0.0.0 \
			--no-browser \
			--allow-root

test: build-dev  ## Run tests
	docker run -it --rm \
		-v ${CURRENT_DIR}:/code \
		--env-file etc/test.env \
		${DEV_IMAGE_TAG} \
		pytest ${TEST}
