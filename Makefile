PROJECT_NAME = semwiki
PROJECT_READABLE_NAME = "Semantic Wikipedia"
PYTHON ?= python3.8
SOURCE_FOLDER = src

MODEL_NAME = universal_sentence_encoder_3

###############################################################################
# ENV SETUP                                                                   #
###############################################################################

.PHONY: env-create
env-create:
	$(PYTHON) -m venv .venv --prompt $(PROJECT_NAME)
	make env-update
	#
	# Don't forget to activate the environment before proceeding! You can run:
	# source .venv/bin/activate


.PHONY: env-update
env-update:
	bash -c "\
		. .venv/bin/activate && \
		pip install wheel && \
		pip install --upgrade -r requirements.txt && \
	"


.PHONY: env-delete
env-delete:
	rm -rf .venv

###############################################################################
# BUILD: linting                                                              #
###############################################################################

COMMIT_HASH ?= $(shell git log --format=%h -n 1 HEAD)
BRANCH_NAME ?= $(shell git branch | grep -e "*" | cut -d " " -f 2)


.PHONY: build-all
build-all: clean radon lint coverage


.PHONY: clean
clean:
	rm -rf build dist *.egg-info
	find $(SOURCE_FOLDER) -name __pycache__ | xargs rm -rf
	find $(TESTS_FOLDER) -name __pycache__ | xargs rm -rf
	find . -name .pytest_cache | xargs rm -rf
	find $(SOURCE_FOLDER) -name '*.pyc' -delete
	rm -rf .coverage


.PHONY: reformat
reformat:
	isort $(SOURCE_FOLDER) cdk tests
	black $(SOURCE_FOLDER) cdk tests


.PHONY: lint
lint:
	$(PYTHON) -m pycodestyle $(SOURCE_FOLDER) cdk tests
	$(PYTHON) -m isort --check-only $(SOURCE_FOLDER) cdk tests
	$(PYTHON) -m black --check $(SOURCE_FOLDER) cdk tests
	$(PYTHON) -m pylint $(SOURCE_FOLDER) cdk
	PYTHONPATH=$(SOURCE_FOLDER) $(PYTHON) -m pylint --disable=missing-docstring,no-self-use tests
	$(PYTHON) -m mypy $(SOURCE_FOLDER) cdk tests


.PHONY: test tests
test tests:
	PYTHONPATH=$(SOURCE_FOLDER) $(PYTHON) -m pytest tests/


.PHONY: coverage
coverage:
	pytest \
		--junitxml=reports/test-result-all.xml \
		--cov=$(SOURCE_FOLDER) \
		--cov-report term-missing \
		--cov-report html:reports/coverage-all.html \
		--cov-report xml:reports/coverage-all.xml


.PHONY: radon
radon:
	radon cc $(SOURCE_FOLDER) --min c
	xenon --max-absolute C --max-modules C --max-average A $(SOURCE_FOLDER)/

##############################################################################################
# DOCKER NAMING                                                                              #
##############################################################################################


BRANCH_NAME_LOWER = $(shell echo $(BRANCH_NAME) | cut -c -70 | tr "[:upper:]" "[:lower:]")

ifeq ("$(BRANCH_NAME)", "master")
        LATEST_TAG = latest
        TAG = $(COMMIT_HASH)
else
        LATEST_TAG = branch-$(BRANCH_NAME_LOWER)
        TAG = branch-$(BRANCH_NAME_LOWER)-$(COMMIT_HASH)
endif

IMAGE = $(DOCKER_IMAGE_NAME):$(TAG)
LATEST = $(DOCKER_IMAGE_NAME):$(LATEST_TAG)
DOCKER_IMAGE_NAME = $(PROJECT_NAME)/$(MODEL_NAME)

###############################################################################
# DOCKER:                                                                     #
###############################################################################
ECR_DOCKER_REGISTRY = 084705978329.dkr.ecr.eu-west-1.amazonaws.com

.PHONY: docker-ecr-login
docker-ecr-login:
	aws ecr get-login-password | docker login --username AWS --password-stdin $(ECR_DOCKER_REGISTRY)

.PHONY: docker-pull
docker-pull: docker-ecr-login
	( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(LATEST) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(LATEST) $(DOCKER_IMAGE_NAME) \
	) || ( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME) $(DOCKER_IMAGE_NAME) \
	)

.PHONY: docker-push
docker-push: docker-ecr-login
	# Push the image as it is
	docker tag $(DOCKER_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(IMAGE)
	docker push $(ECR_DOCKER_REGISTRY)/$(IMAGE)
	# Update latest
	docker tag $(DOCKER_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(LATEST)
	docker push $(ECR_DOCKER_REGISTRY)/$(LATEST)


.PHONY: docker-image
docker-image:
	cd universal-sentence-encoder && \
	docker build \
		--cache-from $(DOCKER_IMAGE_NAME) \
		-t $(DOCKER_IMAGE_NAME) \
		.


.PHONY: docker-create-ecr-repo
docker-create-ecr-repo:
	aws ecr create-repository --repository-name $(PROJECT_NAME)/$(MODEL_NAME) \
	--image-scanning-configuration scanOnPush=true \
	--region eu-west-1


###############################################################################
# API SERVER:                                                                 #
###############################################################################
API_NAME = wikisemantic-api
API_IMAGE = $(DOCKER_API_IMAGE_NAME):$(TAG)
LATEST_API = $(DOCKER_API_IMAGE_NAME):$(LATEST_TAG)
DOCKER_API_IMAGE_NAME = $(PROJECT_NAME)/$(API_NAME)

.PHONY: docker-api-pull
docker-api-pull: docker-ecr-login
	( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(LATEST_API) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(LATEST_API) $(DOCKER_API_IMAGE_NAME) \
	) || ( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(DOCKER_API_IMAGE_NAME) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(DOCKER_API_IMAGE_NAME) $(DOCKER_API_IMAGE_NAME) \
	)

.PHONY: docker-api-push
docker-api-push: docker-ecr-login
	# Push the image as it is
	docker tag $(DOCKER_API_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(API_IMAGE)
	docker push $(ECR_DOCKER_REGISTRY)/$(API_IMAGE)
	# Update latest
	docker tag $(DOCKER_API_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(LATEST_API)
	docker push $(ECR_DOCKER_REGISTRY)/$(LATEST_API)


.PHONY: docker-api-image
docker-api-image:
	docker build \
		--cache-from $(DOCKER_API_IMAGE_NAME) \
		-t $(DOCKER_API_IMAGE_NAME) \
		.


.PHONY: docker-create-api-ecr-repo
docker-create-api-ecr-repo:
	aws ecr create-repository --repository-name $(PROJECT_NAME)/$(API_NAME) \
	--image-scanning-configuration scanOnPush=true \
	--region eu-west-1


###############################################################################
# ELASTICSEARCH:                                                              #
###############################################################################
DOCKER_ES_IMAGE = elasticsearch
DOCKER_CONTAINER = elastic-semwiki
ES_IMAGE = amazon/opendistro-for-elasticsearch:1.13.1


.PHONY: es-image
es-image:
	cd elasticsearch && \
	docker build \
		--cache-from $(DOCKER_ES_IMAGE) \
		-t $(DOCKER_ES_IMAGE) \
		.

.PHONY: es-start
es-start:
	docker run --name $(DOCKER_CONTAINER) -d -p 9200:9200 -p 9600:9600 -p 5601:5601 -e "discovery.type=single-node" $(ES_IMAGE)

.PHONY: es-stop
es-stop:
	docker stop $(DOCKER_CONTAINER)
	docker rm $(DOCKER_CONTAINER)

.PHONY: kibana-start
kibana-start:
	cd elasticsearch && docker-compose up -d

.PHONY: kibana-stop
kibana-stop:
	cd elasticsearch && docker-compose stop


###############################################################################
# LAMBDAS:                                                                    #
###############################################################################
# https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency

LAMBDA_INDEXER_ROLE = arn:aws:iam::084705978329:role/lambda-indexer


.PHONY: lambda-indexer-package
lambda-indexer-package:
	cd src/lambda_indexer/package && zip -r ../lambda_indexer.zip . && cd .. && \
	zip -g lambda_indexer.zip lambda_function.py


.PHONY: lambda-indexer-create
lambda-indexer-create: lambda-indexer-package
	aws lambda create-function --function-name lambda_indexer \
		--zip-file fileb://lambda_indexer.zip \
		--handler lambda_function.lambda_handler \
		--runtime python3.8 \
		--role $(LAMBDA_INDEXER_ROLE)


.PHONY: lambda-indexer-update
lambda-indexer-update: lambda-indexer-package
	aws lambda update-function-code --function-name lambda_indexer --zip-file fileb://lambda_indexer.zip
