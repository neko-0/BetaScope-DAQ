FROM rootproject/root:6.28.00-ubuntu22.04
LABEL maintainer.name="SCIPP UFSD team"
LABEL maintainer.email="yuzhao@ucsc.edu"
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND noninteractive
COPY packages packages
# COPY collinearw.tar.gz collinearw.tar.gz
# COPY setup.sh setup.sh
# COPY configs configs
RUN apt-get -y update \
    && apt-get install -y --no-install-recommends apt-utils \
    && apt-get -y install $(cat packages) 
    # && rm /bin/sh && ln -s /bin/bash /bin/sh \
# creating python venv
RUN ["python", "-m", "pip", "install", "--upgrade", "pip"]
RUN ["python", "-m", "venv", "py3"]
# installing GPIB-linux
RUN git clone https://git.code.sf.net/p/linux-gpib/git linux-gpib-git
    # && cd linux-gpib-git \
    # && cd linux-gpib-kernel && make -j && make install && cd .. \
    # && cd linux-gpib-user && make -j && make install \
# intalling Waveform analysis codes
RUN git clone https://github.com/neko-0/WaveformAna \
    && source WaveformAna/setup.sh \
    && cmake --build $WAVEANA_BUILD_DIR
# installing BetaScope-DAQ
RUN git clone -b update/restructure https://github.com/neko-0/BetaScope-DAQ \
    && source py3/bin/activate \
    && cd BetaScope-DAQ \
    && python -m pip install -e .
# installing collinearw python packages
# RUN mkdir collinearw \
#     && tar xf collinearw.tar.gz -C collinearw --strip-components=1 \
#     && source py3/bin/activate \
#     && cd collinearw \
#     && python -m pip install -e .
CMD ["/bin/bash"]