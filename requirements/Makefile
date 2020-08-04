.PHONY: all check clean

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

all: $(outputs)

%.txt: %.in
	docker build \
		-f $(shell pwd)/../deployment/Dockerfile \
		--target pip_tools \
		-t pip_compile_docker \
		.
	docker run --rm -it \
		-w /code \
		-v $(shell pwd):/code \
		pip_compile_docker \
		pip-compile -v \
			--output-file $@ $<

check:
	@which pip-compile > /dev/null

clean: check
	- rm *.txt
