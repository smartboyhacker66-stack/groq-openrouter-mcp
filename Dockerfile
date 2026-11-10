FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ARG KOTLIN_VERSION=2.0.21
RUN curl -fsSL "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" -o /tmp/kotlin.zip \
 && unzip -q /tmp/kotlin.zip -d /opt \
 && rm /tmp/kotlin.zip
ENV PATH="/opt/kotlinc/bin:${PATH}"
ENV JAVA_OPTS="-Xmx300m"

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY server.py .

CMD ["python3", "server.py"]
