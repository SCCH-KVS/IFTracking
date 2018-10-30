FROM continuumio/miniconda

ENTRYPOINT ["/bin/bash", "-c" ]

EXPOSE 5000

RUN apt-get update && apt-get install -y libpq-dev build-essential libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# Add anaconda environment files
ADD environment.yml /envs/environment.yml
WORKDIR /envs

# Create anaconda environment
RUN [ "conda", "env", "create" ]

# Activate environment
RUN [ "/bin/bash", "-c", "source activate py2.7" ]

# Set working directory
WORKDIR /if-tracking

#CMD [ "source activate py2.7" ] # && exec python app.py