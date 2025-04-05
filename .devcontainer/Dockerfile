FROM rapidsai/base:24.06-cuda12.2-py3.11
USER root
RUN ["sh", "-c", "apt-get update && apt-get install -y gcc make wget unzip"]
RUN ["sh", "-c", "conda install -c conda-forge -y libta-lib"]
USER rapids
RUN ["sh", "-c", "pip install ccxt python-binance ipykernel TA-Lib altair black"]
RUN ["sh", "-c", "conda install -c conda-forge -y pymc>-5"]
RUN ["sh", "-c", "conda install -c conda-forge -y numpyro"]
CMD [ "sleep", "infinity" ]
