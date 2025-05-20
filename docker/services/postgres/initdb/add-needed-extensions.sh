#!/bin/bash

set -e
set -u

function create_extension() {
	local extension=$1
	echo "  Creating extension '$extension'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$POSTGRES_DB" <<-EOSQL
	    CREATE EXTENSION $extension;
EOSQL
}

function show_extensions() {
	echo "  Show extensions"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  	    SELECT * FROM pg_catalog.pg_extension;
EOSQL
}

if [ -n "POSTGRES_EXTENSIONS" ]; then
	echo "Extensions creation requested: $POSTGRES_EXTENSIONS"
	for extension in $(echo $POSTGRES_EXTENSIONS | tr ',' ' '); do
		create_extension $extension
	done
	echo "Extensions created"
	show_extensions
	echo "  Finish work ------------------------------------------------------------------"
fi
