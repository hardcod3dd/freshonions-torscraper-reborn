FROM debian:trixie-slim
RUN apt-get update -qq && apt-get install -y -qq tor && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/lib/tor/hidden_service && \
    chown -R debian-tor:debian-tor /var/lib/tor && \
    chmod 700 /var/lib/tor/hidden_service
COPY torrc /etc/tor/torrc
USER debian-tor
CMD ["tor", "-f", "/etc/tor/torrc"]
