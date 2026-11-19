FROM node:20-slim

WORKDIR /workspace/typescript/futureagi

COPY typescript/futureagi/package.json typescript/futureagi/package-lock.json ./
RUN npm ci --ignore-scripts

COPY typescript/tsconfig.base*.json /workspace/typescript/
COPY typescript/futureagi/tsconfig*.json ./
COPY typescript/futureagi/src ./src
COPY typescript/futureagi/tests/compliance ./tests/compliance

ENV PORT=8080

CMD ["npx", "tsx", "tests/compliance/adapter.ts"]
