FROM rapidsai/base:24.04a-cuda12.2-py3.11
USER root
RUN ["sh", "-c", "apt-get update && apt-get install -y gcc make wget"]
RUN ["sh", "-c", "conda install -c conda-forge -y libta-lib"]
USER rapids
CMD [ "sleep", "infinity" ]