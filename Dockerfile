FROM debian:stable
RUN apt-get -y update \
    && apt-get -y install python3 \
                          python3-pydbus \
                          python3-pip \
                          ca-certificates
RUN pip3 install -U PyYAML
ENV SCRIPT_DIR=/opt/systemd-monitor/bin
RUN mkdir -p $SCRIPT_DIR
COPY config/systemd-monitor.yaml /etc/
COPY monitor/monitor.py $SCRIPT_DIR/monitor.py
WORKDIR $SCRIPT_DIR
CMD [ "python3", "./monitor.py", "/etc/systemd-monitor.yaml" ]