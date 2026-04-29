FROM rapidsai/base:26.04-cuda13-py3.14
USER root
RUN ["sh", "-c", "apt-get update && apt-get install -y gcc make wget unzip apt-transport-https lsb-release"]
RUN wget https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb -O /tmp/packages-microsoft-prod.deb && \
    dpkg -i /tmp/packages-microsoft-prod.deb && \
    rm /tmp/packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-runtime-8.0
RUN ["sh", "-c", "conda install -c conda-forge -y libta-lib"]
USER rapids

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
RUN ["sh", "-c", "pip install ccxt python-binance ipykernel TA-Lib altair"]
RUN ["sh", "-c", "conda install -c conda-forge -y pymc>-5"]
RUN ["sh", "-c", "conda install -c conda-forge -y numpyro"]
CMD [ "sleep", "infinity" ]
