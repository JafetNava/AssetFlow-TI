import os
import sqlite3

from datetime import datetime


def create_backup(
    database_path,
    backup_directory,
    max_backups=30
):
    os.makedirs(
        backup_directory,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_name = (
        f"DB_AssetFlow_TI_{timestamp}.db"
    )

    backup_path = os.path.join(
        backup_directory,
        backup_name
    )

    source = sqlite3.connect(
        database_path
    )

    destination = sqlite3.connect(
        backup_path
    )

    try:
        source.backup(destination)

    finally:
        destination.close()
        source.close()

    cleanup_old_backups(
        backup_directory,
        max_backups
    )

    return backup_path


def cleanup_old_backups(
    backup_directory,
    max_backups=30
):
    if not os.path.exists(
        backup_directory
    ):
        return

    backups = []

    for filename in os.listdir(
        backup_directory
    ):
        if (
            filename.startswith(
                "DB_AssetFlow_TI_"
            )
            and filename.endswith(".db")
        ):
            full_path = os.path.join(
                backup_directory,
                filename
            )

            backups.append(
                (
                    full_path,
                    os.path.getmtime(
                        full_path
                    )
                )
            )

    backups.sort(
        key=lambda item: item[1],
        reverse=True
    )

    for full_path, _ in backups[
        max_backups:
    ]:
        os.remove(full_path)


def list_backups(
    backup_directory
):
    if not os.path.exists(
        backup_directory
    ):
        return []

    backups = []

    for filename in os.listdir(
        backup_directory
    ):
        if not (
            filename.startswith(
                "DB_AssetFlow_TI_"
            )
            and filename.endswith(".db")
        ):
            continue

        full_path = os.path.join(
            backup_directory,
            filename
        )

        size_bytes = os.path.getsize(
            full_path
        )

        modified = datetime.fromtimestamp(
            os.path.getmtime(
                full_path
            )
        )

        backups.append({
            "filename": filename,
            "size": format_file_size(
                size_bytes
            ),
            "created": modified.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "timestamp": modified.timestamp()
        })

    backups.sort(
        key=lambda item: item["timestamp"],
        reverse=True
    )

    return backups


def format_file_size(
    size_bytes
):
    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return (
            f"{size_bytes / 1024:.1f} KB"
        )

    return (
        f"{size_bytes / (1024 ** 2):.1f} MB"
    )


def ensure_daily_backup(
    database_path,
    backup_directory,
    max_backups=30
):
    os.makedirs(
        backup_directory,
        exist_ok=True
    )

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    prefix = (
        f"DB_AssetFlow_TI_{today}_"
    )

    for filename in os.listdir(
        backup_directory
    ):
        if (
            filename.startswith(prefix)
            and filename.endswith(".db")
        ):
            return None

    return create_backup(
        database_path,
        backup_directory,
        max_backups
    )