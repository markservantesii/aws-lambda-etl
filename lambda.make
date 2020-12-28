

.PHONY: clean directories lambdas lambda-layers
	#setup flows tasks templates clean build deploy destroy

# load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif



DIRS:= lambda/deployment-packages

# Lambda deployment packages
LAMBDA_NAMES:= my-lambda-function 
LAMBDA_PACKAGES=$(LAMBDA_NAMES:%=lambda/deployment-packages/%.zip)

# Lambda Layers
LAMBDA_LAYER_NAMES:=pandas
LAMBDA_LAYERS_ZIPS:= $(LAMBDA_LAYER_NAMES:%=lambda/layers/%-layer.zip)
LAMBDA_LAYERS_DOCKERFILE:=lambda/layers/Dockerfile



# ======== SETUP RULES =========
# rules for creating directories
$(DIRS):
	mkdir -p $@

directories: $(DIRS)


# ======== LAMBDA PACKAGES and LAYERS RULES ===========

# rules for creating lambdas
lambdas: directories $(LAMBDA_PACKAGES)

# rule for creating lambda deployment packages
lambda/deployment-packages/%.zip:
	python scripts/build_lambda_package.py --lambda-name $*


# rules for creating lambda-layers
lambda-layers: $(LAMBDA_LAYERS_ZIPS)

# rule to create lambda layers zip files
lambda/layers/%-layer.zip: directories
	docker build \
		--file $(LAMBDA_LAYERS_DOCKERFILE) \
		--tag $*-layer \
		lambda/layers/$*
	$(eval CONTAINER=$(shell docker run -d $*-layer false))
	docker cp $(CONTAINER):/opt/python python
	docker rm $(CONTAINER)
	find python -name '__pycache__' -exec rm -fr {} +
	rm -rf python/*.dist-info python/*.pyc
	zip -r9 $@ python
	rm -rf python


# ===== CLEAN UP RULES =========

# rules for cleaning up
clean:
	rm -rf lambda/deployment-packages
	rm -rf lambda/layers/pandas-layer.zip


