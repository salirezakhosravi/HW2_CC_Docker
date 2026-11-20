# TODO: Explain these five instructions line by line in the report.
# What layer does each one create, and what breaks if that line is missing?
#
# This is the order from the assignment: the whole directory is copied, then dependencies are installed.
# Change the order before you submit. The file in the repository must be the corrected order.
# Put both the before and after Dockerfiles in the report.
#
# TODO: Split copy and install so that a change to app.py, with requirements.txt unchanged,
# leaves the pip install layer CACHED on the second build.
# Build once, change a single comment line in app.py, then build again.
#
# TODO: Also build a smaller image.
# A lighter base, dropping extra files, or a multi-stage build is enough.
# The slim tag must be smaller than the full tag.
# Push only slim to ghcr.io/<username>/cc-hello:slim,
# delete the local image, pull that tag again, and run it.
#
# Build and run outside this file:
#   docker build -t full .
#   docker run --rm full
#   docker build -t slim .
#   docker images
#   docker push ghcr.io/<username>/cc-hello:slim

FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
