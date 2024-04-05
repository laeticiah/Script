 # Set base image (host OS)
FROM python:3.9

# Set the working directory in the container
WORKDIR /code

# Copy dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN python -m venv .venv && \
    /bin/bash -c "source .venv/bin/activate" && \
    pip install --upgrade -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Command to run on container start
CMD [ "sh", "-c", "source .venv/bin/activate && python gh_crawler.py laeticiah config.yaml output.csv"]
