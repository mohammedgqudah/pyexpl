# Python Explorer
Quickly test python programs across different versions.

> This is a personal tool and is not intended for a production deployment. I host my own instance for personal use.

<img width="3408" height="2083" alt="image" src="https://github.com/user-attachments/assets/ba2f2b13-fa40-4d58-8023-0a4997052932" />

# Running
```
make build
docker run --cgroupns host --rm -p 8000:8000 --privileged -it pyexpl:latest
```

# Testing
Tests are run inside the docker container
```
make test
```
