# Python Explorer
Quickly test python programs across different versions.

> Still under development and it's not safe to run arbitrary code yet.

<img width="3511" height="2071" alt="image" src="https://github.com/user-attachments/assets/3efc3bc0-ea4b-47b9-81d0-0344df7dff1e" />

# Running
```
make docker-build
docker run --cgroupns host --rm -p 8000:8000 --privileged -it pyexpl:latest
```

# Testing
Tests are run inside the docker container
```
make test
```
