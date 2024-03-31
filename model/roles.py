"""Data file containing important info for building the role structure"""

from flask_security import datastore

ROLE_VER = 0.1
roles: list[dict] = [
    {
        "name": "admin",
        "description": "Admin role",
        "permissions": [
            "role-manage",
            "user-manage",
            "suggestion-manage",
            "anime-manage",
        ],
    },
    {
        "name": "user",
        "description": "Default user role",
        "permissions": ["suggestion-vote", "suggestion-create"],
    },
]


def init_roles(data_store: datastore) -> bool:
    """
    Initializes roles

    Param:
        data_store: Datastore - datastore to initialize in

    Returns:
        bool - True if init was succesful, False otherwise
    """
    data_store.role_model.query.delete()
    for role in roles:
        ret: bool = data_store.create_role(
            name=role["name"],
            permissions=role["permissions"],
            description=role["description"],
        )
        if not ret:
            return False

    data_store.commit()
    return True