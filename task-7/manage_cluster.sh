#!/bin/bash

if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${YELLOW}======== $1 ========${NC}\n"
}

check_status() {
    print_header "Cluster Status"
    docker exec $CASSANDRA_SEED_CONTAINER nodetool status
}

check_node_status() {
    NODE_NUM=$1
    NODE_CONTAINER=$(get_node_container $NODE_NUM)
    print_header "Status of Node $NODE_NUM ($NODE_CONTAINER)"
    
    # Check if container is running
    CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' $NODE_CONTAINER 2>/dev/null || echo "not found")
    echo -e "Container status: ${GREEN}$CONTAINER_STATUS${NC}"
    
    # If container is running, check Cassandra status
    if [ "$CONTAINER_STATUS" == "running" ]; then
        # Try to connect to the node with nodetool
        if docker exec $NODE_CONTAINER nodetool status &>/dev/null; then
            echo -e "Cassandra status: ${GREEN}RUNNING${NC}"
            echo -e "\nNode Cassandra status:"
            docker exec $NODE_CONTAINER nodetool status
        else
            echo -e "Cassandra status: ${RED}NOT RESPONDING${NC}"
            echo -e "\nLast 10 lines of logs:"
            docker logs --tail 10 $NODE_CONTAINER
        fi
    fi
}

connect_cqlsh() {
    print_header "Connecting to Cassandra with cqlsh"
    docker exec -it $CASSANDRA_SEED_CONTAINER cqlsh -u $CASSANDRA_USER -p $CASSANDRA_PASSWORD
}

if [ $# -eq 0 ]; then
    print_header "Cassandra Cluster Management Script"
    echo "Usage: $0 [command]"
    echo -e "\nAvailable commands:"
    echo "  status          - Show cluster status using nodetool"
    echo "  node-status N   - Show detailed status of node N (e.g. 1, 2)"
    echo "  cqlsh           - Connect to the cluster using cqlsh"
    echo "  start           - Start all containers"
    echo "  stop            - Stop all containers"
    echo "  restart         - Restart all containers"
    echo "  logs            - Show logs from all containers"
    echo "  disconnect NODE - Disconnect a node (e.g. 1, 2)"
    echo "  reconnect NODE  - Reconnect a node (e.g. 1, 2)"
    echo "  run SCRIPT      - Run a Python script using docker compose run (e.g. main.py)"
    echo "  ring            - Show the token ring information"
    echo "  endpoints KEY   - Show endpoints for a key (use with caution!)"
    echo "  repair          - Run repair on the seed node"
    echo "  repair-node N   - Run repair on a specific node (e.g. 1, 2)"
    echo "  info            - Show detailed information about the cluster"
    echo -e "\nExamples:"
    echo "  $0 status"
    echo "  $0 node-status 2"
    echo "  $0 disconnect 2"
    echo "  $0 run test_consistency.py"
    exit 0
fi

get_node_container() {
    local node_num=$1
    if [ "$node_num" == "1" ]; then
        echo $CASSANDRA_NODE1_CONTAINER
    elif [ "$node_num" == "2" ]; then
        echo $CASSANDRA_NODE2_CONTAINER
    else
        echo "Invalid node number: $node_num"
        exit 1
    fi
}

case "$1" in
    status)
        check_status
        ;;
    node-status)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a node number (1 or 2)${NC}"
            exit 1
        fi
        check_node_status $2
        ;;
    cqlsh)
        connect_cqlsh
        ;;
    start)
        print_header "Starting Cassandra Cluster"
        docker compose up -d
        ;;
    stop)
        print_header "Stopping Cassandra Cluster"
        docker compose down
        ;;
    restart)
        print_header "Restarting Cassandra Cluster"
        docker compose down
        docker compose up -d
        ;;
    logs)
        print_header "Showing Logs"
        docker compose logs --tail=100 -f
        ;;
    disconnect)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a node number (1 or 2)${NC}"
            exit 1
        fi
        NODE_CONTAINER=$(get_node_container $2)
        print_header "Disconnecting Node $2 ($NODE_CONTAINER)"
        docker stop $NODE_CONTAINER
        sleep 5
        check_status
        ;;
    reconnect)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a node number (1 or 2)${NC}"
            exit 1
        fi
        NODE_CONTAINER=$(get_node_container $2)
        print_header "Reconnecting Node $2 ($NODE_CONTAINER)"
        docker start $NODE_CONTAINER
        
        echo -e "${YELLOW}Waiting 30 seconds for node to fully rejoin the cluster...${NC}"
        sleep 30
        
        print_header "Node Logs After Reconnect (last 10 lines)"
        docker logs --tail 10 $NODE_CONTAINER
        
        print_header "Gossip Info from Seed Node"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool gossipinfo
        
        check_status
        ;;
    run)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a Python script to run${NC}"
            exit 1
        fi
        print_header "Running $2"
        docker compose run --rm -it app python /app/$2
        ;;
    ring)
        print_header "Token Ring Information"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool ring
        ;;
    endpoints)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a key${NC}"
            exit 1
        fi
        print_header "Endpoints for key $2"
        echo -e "${YELLOW}Note: This is a simplified version. In a real scenario, you'd need to specify keyspace and table.${NC}"
        # This is for demonstration purposes only - in a real scenario, you'd need more specifics
        docker exec $CASSANDRA_SEED_CONTAINER nodetool getendpoints ${CASSANDRA_RF3_KEYSPACE:-keyspace_rf3} test_data $2
        ;;
    repair)
        print_header "Running Repair"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool repair
        ;;
    repair-node)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a node number (1 or 2)${NC}"
            exit 1
        fi
        NODE_CONTAINER=$(get_node_container $2)
        print_header "Running Repair on Node $2 ($NODE_CONTAINER)"
        docker exec $NODE_CONTAINER nodetool repair
        ;;
    info)
        print_header "Cluster Information"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool info
        echo -e "\n${YELLOW}Datacenter and Rack Information:${NC}"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool describecluster
        echo -e "\n${YELLOW}Compaction Statistics:${NC}"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool compactionstats
        echo -e "\n${YELLOW}Gossip Information:${NC}"
        docker exec $CASSANDRA_SEED_CONTAINER nodetool gossipinfo
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo "Use '$0' without arguments to see available commands"
        exit 1
        ;;
esac

exit 0 