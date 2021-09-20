PROJECT_NAME = semwiki
PROJECT_READABLE_NAME = "Semantic Wikipedia"
PYTHON ?= python3
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
		pip install --upgrade -r requirements.txt \
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
	isort $(SOURCE_FOLDER) lambda_indexer infrastructure tests
	black $(SOURCE_FOLDER) lambda_indexer infrastructure tests


.PHONY: lint
lint:
	$(PYTHON) -m pycodestyle $(SOURCE_FOLDER) lambda_indexer infrastructure tests
	$(PYTHON) -m isort --check-only $(SOURCE_FOLDER) lambda_indexer infrastructure tests
	$(PYTHON) -m black --check $(SOURCE_FOLDER) lambda_indexer infrastructure tests
	$(PYTHON) -m pylint $(SOURCE_FOLDER) lambda_indexer infrastructure
	PYTHONPATH=$(SOURCE_FOLDER) $(PYTHON) -m pylint --disable=missing-docstring,no-self-use tests
	$(PYTHON) -m mypy $(SOURCE_FOLDER) lambda_indexer tests


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

.PHONY: docker-embedder-pull
docker-embedder-pull: docker-ecr-login
	( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(LATEST) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(LATEST) $(DOCKER_IMAGE_NAME) \
	) || ( \
					docker pull $(ECR_DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME) \
					&& docker tag $(ECR_DOCKER_REGISTRY)/$(DOCKER_IMAGE_NAME) $(DOCKER_IMAGE_NAME) \
	)

.PHONY: docker-embedder-push
docker-embedder-push: docker-ecr-login
	# Push the image as it is
	docker tag $(DOCKER_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(IMAGE)
	docker push $(ECR_DOCKER_REGISTRY)/$(IMAGE)
	# Update latest
	docker tag $(DOCKER_IMAGE_NAME) $(ECR_DOCKER_REGISTRY)/$(LATEST)
	docker push $(ECR_DOCKER_REGISTRY)/$(LATEST)


.PHONY: docker-embedder-image
docker-embedder-image:
	cd universal-sentence-encoder && \
	docker build \
		--cache-from $(DOCKER_IMAGE_NAME) \
		-t $(DOCKER_IMAGE_NAME) \
		.


.PHONY: docker-create-ecr-embedder
docker-create-ecr-embedder:
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


.PHONY: docker-create-ecr-api
docker-create-ecr-api:
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
LAMBDA_INDEXER_ROLE = arn:aws:iam::084705978329:role/lambda-indexer

INDEXING_LAMBDA_QUERY = "Stacks[0].Outputs[?OutputKey=='IndexingLambdaName'].OutputValue"

INDEXING_LAMBDA_NAME = $$(aws cloudformation describe-stacks --stack-name $(STACK_INDEXING) \
						--query $(INDEXING_LAMBDA_QUERY) --output text)


.PHONY: lambda-indexer-package
lambda-indexer-package:
	pip install -r lambda_indexer/requirements.txt --target lambda_indexer/package/
	cd lambda_indexer/package && zip -r ../lambda_indexer.zip . && cd .. && \
	zip -g lambda_indexer.zip lambda_function.py util.py


.PHONY: lambda-indexer-create
lambda-indexer-create: lambda-indexer-package
	aws lambda create-function --function-name lambda_indexer \
		--zip-file fileb://lambda_indexer.zip \
		--handler lambda_function.lambda_handler \
		--runtime python3.8 \
		--role $(LAMBDA_INDEXER_ROLE)


.PHONY: lambda-indexer-update
lambda-indexer-update: lambda-indexer-package
	cd lambda_indexer && \
	aws lambda update-function-code --function-name $(INDEXING_LAMBDA_NAME) --zip-file fileb://lambda_indexer.zip

###############################################################################
# CloudFormation:                                                             #
###############################################################################
STACK_ELASTICSEARCH = ESCluster
STACK_EMBEDDING_SERVICE = EmbeddingService
STACK_INDEXING = WikiReferencing
STACK_API_SERVICE = SearchAPIService

CLUSTER_ARN_QUERY = "Stacks[0].Outputs[?OutputKey=='ClusterArn'].OutputValue"
TASK_QUERY = "taskArns[0]"
NETWORK_INTERFACE_QUERY = "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value"
PUBLIC_IP_QUERY = "NetworkInterfaces[0].Association.PublicIp"

ELASTICSEARCH_ENDPOINT_QUERY = "Stacks[0].Outputs[?OutputKey=='ESDomainEndpoint'].OutputValue"

EMBEDDER_CLUSTER_ARN = $$(aws cloudformation describe-stacks --stack-name $(STACK_EMBEDDING_SERVICE) \
				--query $(CLUSTER_ARN_QUERY) --output text)
EMBEDDER_TASK = $$(aws ecs list-tasks --cluster $(EMBEDDER_CLUSTER_ARN) --query $(TASK_QUERY) --output text)
EMBEDDER_NETWORK_INTERFACE = $$(aws ecs describe-tasks --cluster $(EMBEDDER_CLUSTER_ARN) --tasks $(EMBEDDER_TASK) \
					--query $(NETWORK_INTERFACE_QUERY) --output text)
EMBEDDER_PUBLIC_IP = $$(aws ec2 describe-network-interfaces --network-interface-id $(EMBEDDER_NETWORK_INTERFACE) \
					--query $(PUBLIC_IP_QUERY) --output text)

ELASTICSEARCH_ENDPOINT = $$(aws cloudformation describe-stacks --stack-name $(STACK_ELASTICSEARCH) \
							--query $(ELASTICSEARCH_ENDPOINT_QUERY) --output text)

API_CLUSTER_ARN = $$(aws cloudformation describe-stacks --stack-name $(STACK_API_SERVICE) \
				--query $(CLUSTER_ARN_QUERY) --output text)
API_TASK = $$(aws ecs list-tasks --cluster $(API_CLUSTER_ARN) --query $(TASK_QUERY) --output text)
API_NETWORK_INTERFACE = $$(aws ecs describe-tasks --cluster $(API_CLUSTER_ARN) --tasks $(API_TASK) \
					--query $(NETWORK_INTERFACE_QUERY) --output text)
API_PUBLIC_IP = $$(aws ec2 describe-network-interfaces --network-interface-id $(API_NETWORK_INTERFACE) \
					--query $(PUBLIC_IP_QUERY) --output text)

.PHONY: cdk-bootstrap-environment
cdk-bootstrap-environment:
	cd infrastructure && PYTHONPATH=../src cdk bootstrap && cd ..


.PHONY: echo-embedder-ip
echo-embedder-ip:
	echo $(EMBEDDER_PUBLIC_IP)

.PHONY: echo-elastic-search-endpoint
echo-elastic-search-endpoint:
	echo $(ELASTICSEARCH_ENDPOINT)

.PHONY: echo-api-ip
echo-api-ip:
	echo $(API_PUBLIC_IP)

###############################################################################
# CDK:                                                                 #
###############################################################################

.PHONY: deploy-es
deploy-es:
	cd infrastructure && PYTHONPATH=../src cdk deploy ESCluster && cd ..

.PHONY: create-es-index
create-es-index:
	python src/scripts.py create-index

.PHONY: deploy-embedder
deploy-embedder:
	cd infrastructure && PYTHONPATH=../src cdk deploy EmbeddingService && cd ..

.PHONY: deploy-referencing
deploy-referencing:
	cd infrastructure && PYTHONPATH=../src cdk deploy WikiReferencing && cd ..

.PHONY: deploy-api
deploy-api:
	cd infrastructure && PYTHONPATH=../src cdk deploy SearchAPIService && cd ..

