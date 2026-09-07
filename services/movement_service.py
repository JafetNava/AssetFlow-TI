def register_movement(
    connection,
    computer_id,
    movement_type,
    description,
    previous_value=None,
    new_value=None
):
    connection.execute(
        """
        INSERT INTO AssetMovements (
            ComputerID,
            MovementType,
            Description,
            PreviousValue,
            NewValue
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            computer_id,
            movement_type,
            description,
            previous_value,
            new_value
        )
    )