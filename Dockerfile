FROM ubuntu:latest
LABEL authors="moriarty"

ENTRYPOINT ["top", "-b"]