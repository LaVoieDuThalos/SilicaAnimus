# using ubuntu LTS version
FROM ubuntu:24.04 AS builder-image

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y python3.12 python3.12-dev python3.12-venv python3-pip python3-wheel build-essential && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# create and activate virtual environment
# using final folder name to avoid path issues with packages
RUN python3 -m venv /home/animus/venv
ENV PATH="/home/animus/venv/bin:$PATH"

# install requirements
COPY src src
COPY README.md .
RUN pip3 install --no-cache-dir --compile -e ./src -vvv

FROM ubuntu:24.04 AS runner-image
RUN apt-get update && apt-get install --no-install-recommends -y python3.12 python3-venv && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home animus
COPY --from=builder-image /home/animus/venv /home/animus/venv

USER animus
RUN mkdir /home/animus/code
WORKDIR /home/animus/code
COPY src/ .

# on s'assu de ne pas coller le fichier .env contenant les secrets dans l'image Docker
# il faut alors utiliser un volume sur le .env au lancement du container : -v .env:/home/animus/SilicaAnimus/.env
RUN rm -f SilicaAnimus/.env

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# activate virtual environment
ENV VIRTUAL_ENV=/home/animus/venv
ENV PATH="/home/animus/venv/bin:$PATH"

CMD ["python3","SilicaAnimus/main.py"]