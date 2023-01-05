# Poetry
FROM public.ecr.aws/lambda/python:3.9 as builder

WORKDIR /work
RUN pip install --upgrade pip && pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -f requirements.txt > requirements.txt
RUN poetry export --without-hashes --dev -f requirements.txt > requirements-dev.txt
RUN pip install -r requirements.txt


# AWS Container
FROM public.ecr.aws/lambda/python:3.9 as lambda

# WORKDIR /work
COPY --from=builder /var/lang/lib/python3.9/site-packages /var/lang/lib/python3.9/site-packages
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY handon_fx ${LAMBDA_TASK_ROOT}/handon_fx
COPY backtesting ${LAMBDA_TASK_ROOT}/backtesting
COPY keys/privkey keys/pubkey ${LAMBDA_TASK_ROOT}/keys/

CMD ["lambda_handler.push_notification"]