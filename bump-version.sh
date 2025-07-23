#!/bin/bash

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
  echo "Please provide a version. Usage: ./bump-version.sh v1.2.3"
  exit 1
fi

echo '__version__ = "'$NEW_VERSION'"' > similarity_api_impl/version.py

echo "Set version in similarity_api_impl/version.py to $NEW_VERSION."