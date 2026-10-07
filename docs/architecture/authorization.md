# Authorization & Role-Based Access Control

- **Roles**: `seeker`, `host`, `admin`.
- **Dynamic Context Switching**: Authorized hosts can switch seamlessly between seeker and host perspectives.
- **Admin Isolation**: Admin endpoints strictly require `is_admin=True` validated server-side.
