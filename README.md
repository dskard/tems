# tems - Test Environment: Mail Server

This repository extends the ideas from https://github.com/camptocamp/docker_smtp with a docker-compose.yml that places all containers on a docker network and a set of test cases that serve as example code for how to interact with the smtp and imap servers to send and receive emails.

Use the included Makefile to launch the environment:

```
make test-env-up
```

Run tests serially:

```
make test
```

Run tests in parallel:

```
make test PYTESTOPTS="-n 5"
```

Run tests in parallel multiple times:

```
make test PYTESTOPTS="-n 15 --count 100"
```

Tear down the containers, networks, and shared volumes

```
make test-env-down
```

