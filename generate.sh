#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
mkdir -p ${SCRIPT_DIR}/openapi-generator
OPENAPI_GENERATOR=${SCRIPT_DIR}/openapi-generator/openapi-generator-cli.sh
curl https://raw.githubusercontent.com/OpenAPITools/openapi-generator/master/bin/utils/openapi-generator-cli.sh > ${OPENAPI_GENERATOR}
chmod +x ${OPENAPI_GENERATOR}
export PYTHON_POST_PROCESS_FILE="yapf -i"
rm -rf "${SCRIPT_DIR}/gen"
${OPENAPI_GENERATOR} generate -c ${SCRIPT_DIR}/config-openapi.yaml
