NAME=happymap

DEVPORT=8080

# Deployment with Kubernetes

# KUBE_CA_PEM_FILE is the path of a certificate file. It automatically set by GitLab
# if you enable Kubernetes integration in a project.
#
# As of this writing, Kubernetes integration can not be set on a group level, so it has to
# be manually set in every project.
# Alternatively, we use a custom KUBE_CA_BUNDLE environment variable, which can be set at
# the group level. In this case, the variable contains the whole content of the certificate,
# which we dump to a temporary file
#
# Check if the KUBE_CA_PEM_FILE exists. Otherwise, create it from KUBE_CA_BUNDLE
KUBE_CA_TEMP=false
ifeq ($(wildcard $(KUBE_CA_PEM_FILE)),) 
	KUBE_CA_PEM_FILE:="$$PWD/.ca.crt"
	CREATED:=$(shell echo -e "$$KUBE_CA_BUNDLE" > $(KUBE_CA_PEM_FILE))
endif 
KUBE_URL=""
KUBE_TOKEN=""
KUBE_NAMESPACE=$(NAME)
KUBECTL=docker run --rm -v $(KUBE_CA_PEM_FILE):/tmp/ca.pem -i lachlanevenson/k8s-kubectl --server="$(KUBE_URL)" --token="$(KUBE_TOKEN)" --certificate-authority="/tmp/ca.pem" -n $(KUBE_NAMESPACE)

CI_PROJECT_NAME=$(NAME)
CI_REGISTRY=docker.io
CI_REGISTRY_USER=gitlab
CI_COMMIT_REF_NAME=master
WEB_IMAGE=registry.cluster.gsi.dit.upm.es/sefarad/happymap/

help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/\(.*:\)\s*##\s*\(.*\)/\1\t\t\2\n/'

config:  ## Load config from the environment. You should run it once in every session before other tasks. Run: eval $(make config)
	@echo ". ../.env || true;"
	@awk '{ print "export " $$0}' .env
	@echo "# Please, run: "
	@echo "# eval \$$(make config)"
# If you need to run a command on the key/value pairs, use this:
# @awk '{ split($$0, a, "="); "echo " a[2] " | base64 -w 0" |& getline b64; print "export " a[1] "=" a[2]; print "export " a[1] "_BASE64=" b64}' .env

deploy: ## Deploy to kubernetes using the credentials in KUBE_CA_PEM_FILE (or KUBE_CA_BUNDLE ) and TOKEN
	@cat k8s/* | envsubst | $(KUBECTL) apply -f -

deploy-check: ## Get the deployed configuration.
	@$(KUBECTL) get deploy,pods,svc,ingress

login: ## Log in to the registry. It will only be used in the server, or when running a CI task locally (if CI_BUILD_TOKEN is set).
ifeq ($(CI_BUILD_TOKEN),)
	@echo "Not logging in to the docker registry" "$(CI_REGISTRY)"
else
	docker login -u gitlab-ci-token -p $(CI_BUILD_TOKEN) $(CI_REGISTRY)
endif

info: ## Print variables. Useful for debugging.
	@echo "#KUBERNETES"
	@echo KUBE_URL=$(KUBE_URL)
	@echo KUBE_CA_PEM_FILE=$(KUBE_CA_PEM_FILE)
	@echo KUBE_CA_BUNDLE=$$KUBE_CA_BUNDLE
	@echo KUBE_TOKEN=$(KUBE_TOKEN)
	@echo KUBE_NAMESPACE=$(KUBE_NAMESPACE)
	@echo KUBECTL=$(KUBECTL)

	@echo "#CI"
	@echo CI_PROJECT_NAME=$(CI_PROJECT_NAME)
	@echo CI_REGISTRY=$(CI_REGISTRY)
	@echo CI_REGISTRY_USER=$(CI_REGISTRY_USER)
	@echo CI_COMMIT_REF_NAME=$(CI_COMMIT_REF_NAME)
	@echo "#DOCKER IMAGES"
	@echo WEB_IMAGE=$(WEB_IMAGE)

#
# For local development
# 

build: ## Build all docker images
	docker-compose build

push: ## Push docker all built docker images to the registry
	docker-compose push

build-%: ## Build a specific image. For example, to build the 'web' image: make build-web
	docker-compose build $*

push-%: ## Push a specific image to the repository. For example, to push the 'web' image: make push-web
	docker-compose build $*

ci: ## Run a task locally like GitLab will run it in the server. For example: make -e action=build ci
	gitlab-runner exec shell ${action}

.PHONY:
	deploy info build push help deploy-check push-% build-% ci
