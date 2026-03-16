#!make

default: help
all: frontend scrapper isup compose-start

frontend: ## Build the wsgi frontend
	@docker build -f frontend.dockerfile . -t fresh/frontend

scrapper: ## Build the scrapper container
	@docker build -f scrapper.dockerfile . -t fresh/scrapper

isup: ## Build the isup container
	@docker build -f isup.dockerfile . -t fresh/isup

compose-start: ## Setup a docker env with all the services
	@CURRENT_UID=$(id -u):$(id -g) docker-compose up

compose-stop: ## stop all the microservices
	@CURRENT_UID=$(id -u):$(id -g) docker-compose down

help: ## Display this information. Default target.
	@echo "Valid targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

clean: ## WARNING: Erased all cached containers db, ...
	@docker-compose rm

check_defined = \
		$(strip $(foreach 1,$1, \
		$(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
		$(if $(value $1),, \
		$(error Undefined $1$(if $2, ($2))))
