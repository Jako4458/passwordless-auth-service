# start by pulling the python image
FROM python:3.10-alpine


ENV running_in_docker=true

# Install dependencies with apk
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    python3-dev

# copy the requirements file into the image
COPY auth/requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install gunicorn
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY /auth /app
COPY /utils /app/utils

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["app.py"]
# CMD ["gunicorn"  , "-b", "0.0.0.0:5000", "app:app"]

# EXPOSE 5000
