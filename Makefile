.PHONY: build docker-export test
build:
	docker build -t pyexpl:latest .

docker-export:
	rm -rf temp
	mkdir temp
	docker container rm -f temp_pyexpl
	docker create --name temp_pyexpl pyexpl:latest
	docker export temp_pyexpl > rootfs.tar
	tar -xf rootfs.tar -C temp

test:
	docker run --rm -v ./tests:/app/tests:ro -v ./src:/app/src:ro --cgroupns host --privileged -it pyexpl:latest uv run pytest $(ARGS)

jail_sh:
	docker run --rm -v ./tests:/app/tests:ro --cgroupns host --privileged -it pyexpl:latest /usr/bin/env nsjail -C nsjail.cfg --time_limit 0 -- /bin/bash
