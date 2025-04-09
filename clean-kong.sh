#!/bin/bash

echo "🧹 Deleting existing routes..."

ROUTES=$(curl -s http://localhost:8001/routes | jq -r '.data[].id')
if [ -z "$ROUTES" ]; then
  echo "⚠️ No routes found or failed to fetch routes"
else
  for route_id in $ROUTES; do
    echo "🔻 Deleting route ID: $route_id"
    curl -s -X DELETE http://localhost:8001/routes/$route_id > /dev/null
  done
fi

echo
echo "🧹 Deleting existing services..."

SERVICES=$(curl -s http://localhost:8001/services | jq -r '.data[].id')
if [ -z "$SERVICES" ]; then
  echo "⚠️ No services found or failed to fetch services"
else
  for service_id in $SERVICES; do
    echo "🔻 Deleting service ID: $service_id"
    curl -s -X DELETE http://localhost:8001/services/$service_id > /dev/null
  done
fi

echo
echo "✅ Cleanup done"
