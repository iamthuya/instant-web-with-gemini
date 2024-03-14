# Python image to use.
FROM python:3.12-slim

# Initialize arguments
ARG USER_NAME=appuser
ARG APP_ROOT=/home/$USER_NAME/code

# Add python local bin to PATH
ENV PATH=$APP_ROOT/.local/bin:$PATH

# Update OS, install packages, create user
RUN apt-get -qq update --fix-missing \ 
    && apt-get -qq install --no-install-recommends -y \
    && apt-get -qq autoremove \
    && apt-get -qq autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log /tmp/* \
    && useradd --create-home $USER_NAME

# Change user and working directory
USER $USER_NAME
RUN mkdir $APP_ROOT
WORKDIR $APP_ROOT

# Install python requirements
COPY requirements.txt ./
RUN pip -q install --no-cache-dir -r requirements.txt \
 && rm requirements.txt

# Copy rest of the code
COPY app.py ./
COPY templates ./templates

EXPOSE 8080

# Run app.py when the container launches
ENTRYPOINT ["python", "app.py"]
