#!/bin/bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
GHTOKEN=$(gh auth token)
BASIC=$(printf 'x-access-token:%s' "$GHTOKEN" | base64)
git -c credential.helper= -c http.https://github.com/.extraheader="AUTHORIZATION: basic ${BASIC}" push --set-upstream origin "$BRANCH"
