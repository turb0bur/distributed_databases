#!/bin/bash
set -e

if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found!"
    exit 1
fi

ES_URL="http://localhost:${ES_PORT:-9200}"
KIBANA_URL="http://localhost:${KIBANA_PORT:-5601}"
WAIT_TIMEOUT_SECONDS=300
WAIT_INTERVAL_SECONDS=5
KIBANA_SYSTEM_USER="kibana_system"

validate_env_vars() {
    local required_vars=("ES_PORT" "KIBANA_PASSWORD" "ELASTICSEARCH_USERNAME" "ELASTICSEARCH_PASSWORD")

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: $var environment variable is not set"
            exit 1
        fi
    done
    echo "Environment variables validated."
}

stop_containers() {
    echo "Stopping existing containers..."
    docker-compose down
}

start_service() {
    local service_name="$1"
    echo "Building and starting ${service_name}..."
    docker-compose up -d "${service_name}"
}

wait_for_elasticsearch() {
    echo "Waiting for Elasticsearch to be ready..."
    until curl -s -f -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} "${ES_URL}/_cat/health" > /dev/null; do
        echo "Elasticsearch is not ready yet, waiting..."
        sleep ${WAIT_INTERVAL_SECONDS}
    done
    echo "Elasticsearch is ready!"
}

wait_for_kibana() {
    echo "Waiting for Kibana to be ready..."
    until curl -s -f "${KIBANA_URL}/api/status" | grep -q '"level":"available"'; do
        echo "Kibana is not ready yet, waiting..."
        sleep ${WAIT_INTERVAL_SECONDS}
    done
    echo "Kibana is ready!"
}

update_kibana_password() {
    echo "Updating Kibana system user password..."
    curl -X POST -u ${ELASTICSEARCH_USERNAME}:${ELASTICSEARCH_PASSWORD} \
        -H "Content-Type: application/json" \
        "${ES_URL}/_security/user/${KIBANA_SYSTEM_USER}/_password" \
        -d "{
            \"password\": \"${KIBANA_PASSWORD}\"
        }"
    echo "Kibana password updated successfully."
}

display_final_message() {
    echo ""
    echo "-----------------------------------------------------"
    echo "Setup Summary:"
    echo "-----------------------------------------------------"
    echo "Application has been started."
    echo "You can access Kibana at ${KIBANA_URL}"
    echo "Username: ${KIBANA_SYSTEM_USER}"
    echo "Password: [The KIBANA_PASSWORD value from your .env file]"
    echo ""
    echo "To view logs from the application: docker compose logs -f app"
    echo "-----------------------------------------------------"
}

main() {
    validate_env_vars
    stop_containers
    
    start_service "elasticsearch"
    wait_for_elasticsearch || exit 1
    
    update_kibana_password
    
    start_service "kibana"
    wait_for_kibana || echo "Warning: Kibana might not be fully ready, but continuing..."
    
    start_service "app"
    
    display_final_message
}

main 