#!/bin/bash

set -e

database_container_name="ras-backend_database_1"

docker exec $database_container_name rm -rf /backup
docker exec $database_container_name mkdir /backup
docker exec $database_container_name pg_dump -U postgres -d rc -f /backup/rc_backup.sql
echo "rc backed up"
docker exec $database_container_name pg_dump -U postgres -d rc -f /backup/student_backup.sql
echo "student backed up"
docker exec $database_container_name pg_dump -U postgres -d rc -f /backup/company_backup.sql
echo "company backed up"
docker exec $database_container_name pg_dump -U postgres -d rc -f /backup/auth_backup.sql
echo "auth backed up"
docker exec $database_container_name pg_dump -U postgres -d rc -f /backup/application_backup.sql
echo "application backed up"

current_datetime=$(date +"%Y-%m-%d_%H-%M-%S")
backup_dir=backup_$current_datetime

mkdir ./backup/$backup_dir
docker cp $database_container_name:/backup ./backup/$backup_dir

backups=($(find "./backup" -maxdepth 1 -type d -printf "%f\n" | sort))

if [ ${#backups[@]} -gt 5 ]; then
    num_to_delete=$((${#backups[@]}-5))

    for ((i=1; i<=$num_to_delete; i++)); do
        echo "Removing old backup - ${backups[$i]}"
        rm -rf "./backup/${backups[$i]}"
    done
    rm -rf "./backup/${backups[1]}"
fi