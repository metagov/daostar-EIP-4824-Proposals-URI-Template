# EIP-4824 Proposals URI API Documentation

This page provides detailed documentation for the API endpoints available in the application, focusing on retrieving proposals for a specific DAO space.

## Endpoints

- **GET /proposals/<space>** - Fetches proposals for a specified DAO space.

    **Parameters:**
    - `space`: String - The DAO space identifier (e.g., "ens.eth") as part of the URL path.
    - `cursor`: Integer (optional) - Used to paginate results based on this cursor. If provided, the API fetches results created after the timestamp denoted by this cursor.
    - `refresh`: Boolean (optional) - If true, forces the endpoint to bypass the cache and refresh the data from the source.
    - `onchain`: String (optional) - If provided, fetches on-chain proposals using the provided organization slug.

    **Description:**
    This endpoint retrieves a list of proposals from the specified DAO space, allowing for pagination if a cursor is provided. It is effective for accessing data in manageable segments when dealing with large datasets. Use the `refresh` parameter to force a refresh of the data and update the cache. The `onchain` parameter fetches on-chain proposals from Tally API if the organization slug is provided.

### Example Usage

- **Request without cursor:**

    ```bash
    GET /proposals/ens.eth
    ```

- **Request with cursor:**

    ```bash
    GET /proposals/ens.eth?cursor=1609459200
    ```

- **Request with refresh:**

    ```bash
    GET /proposals/ens.eth?refresh=true
    ```

- **Request with onchain:**

    ```bash
    GET /proposals/ens.eth?onchain=your_slug_here
    ```

- **Request with refresh and onchain:**

    ```bash
    GET /proposals/ens.eth?refresh=true&onchain=your_slug_here
    ```
