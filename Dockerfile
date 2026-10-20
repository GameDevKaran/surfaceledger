FROM public.ecr.aws/lambda/python:3.14@sha256:252cbb0879717b1c049b9f909d86d06d88e129f3208386d7ba1189d535f5f981
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && python -c "import cv2; assert cv2.__version__.split('.')[0]=='5'; print(cv2.__version__)"
COPY surfaceledger ${LAMBDA_TASK_ROOT}/surfaceledger
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/lambda_handler.py
COPY web ${LAMBDA_TASK_ROOT}/web
ARG SOURCE_COMMIT=development-uncommitted
ENV SURFACELEDGER_SOURCE_COMMIT=${SOURCE_COMMIT}
LABEL org.opencontainers.image.title="SurfaceLedger" org.opencontainers.image.revision="${SOURCE_COMMIT}"
CMD ["lambda_handler.handler"]
