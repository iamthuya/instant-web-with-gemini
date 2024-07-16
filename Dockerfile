# Python image to use.
FROM python:3.12-slim

# Initialize arguments
ARG USER_NAME=docker
ARG APP_ROOT=/home/$USER_NAME/app

# Add python local bin to PATH
ENV PATH=$APP_ROOT/.local/bin:$PATH

# Update OS, install packages, create user
RUN apt-get -qq update --fix-missing \ 
    && apt-get -qq install --no-install-recommends -y \
    && apt-get -qq autoremove \
    && apt-get -qq autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log /tmp/* \
    && useradd --create-home $USER_NAME

RUN pip -q install --no-cache-dir gunicorn 

# Change user and working directory
USER $USER_NAME
RUN mkdir $APP_ROOT
WORKDIR $APP_ROOT

# Install python requirements
COPY requirements.txt ./
RUN pip -q install --no-cache-dir -r requirements.txt \
 && rm requirements.txt

# Copy rest of the code
COPY app.py ./app.py
COPY templates ./templates
COPY static/tailwind-output.css ./static/tailwind-output.css
COPY static/style.css ./static/style.css

EXPOSE 8080

# Run serve with gunicorn when the container launches
CMD ["gunicorn", "-w", "4", "--timeout", "240", "--bind", "0.0.0.0:8080", "app:app"] 
