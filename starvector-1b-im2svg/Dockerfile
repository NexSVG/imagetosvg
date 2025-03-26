# Read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

FROM python:3.11
RUN apt-get update && apt-get install -y openssh-client sshpass

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"


WORKDIR /app

COPY --chown=user . /app
RUN pip install -e .

RUN chmod +x ./start.sh
CMD ["./start.sh"]
