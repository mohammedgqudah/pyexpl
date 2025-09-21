.PHONY: docker-build
docker-build:
	sudo docker build -t pyexpl:latest .

docker-export:
	rm -rf temp
	mkdir temp
	sudo docker container rm -f temp_pyexpl
	sudo docker create --name temp_pyexpl pyexpl:latest
	sudo docker export temp_pyexpl > rootfs.tar
	tar -xf rootfs.tar -C temp

test:
	sudo docker run -v ./tests:/app/tests:ro --cgroupns host --privileged -it pyexpl:latest uv run pytest
